# visa_tool

Tự động khai đơn xin visa Trung Quốc trên COVA (`consular.mfa.gov.cn`):
gọi lần lượt các API của từng trang form, sinh giấy tờ đi kèm (khách sạn,
vé máy bay, xác nhận trung tâm visa, thư mời, lịch trình) và upload hồ sơ.
Hỗ trợ các loại visa **L15, L30, M, Q1, Q2, F**.

## Cấu trúc

| Thư mục / file | Vai trò |
|---|---|
| `server.py` | FastAPI. `POST /run` chạy flow khai đơn; các endpoint phụ cho R2, PDF, email duyệt (`/han-approval/*`), đồng bộ trạng thái |
| `main.py` | `build_case()` chuẩn hoá payload `/run`, `main()` gọi flow |
| `flows/run_flow.py` | Chạy các step theo thứ tự, trả kết quả / lỗi |
| `flows/flow_step/` | Luồng chung: 1 validate · 2 token + OCR · 3 draft · 4 person + apply · 5 work/education/family · 6 travel + giấy tờ · 7 upload · 8 lưu DB |
| `flows/flow_payloads.py` | Dựng body cho từng API COVA |
| `visa_types/` | **Khác biệt giữa các loại visa** (mỗi loại 1 profile) — xem [visa_types/README.md](visa_types/README.md) |
| `api/` | Mỗi file bọc 1 endpoint COVA / R2 |
| `generate_file/` + `resources/*.docx` | Render giấy tờ từ template DOCX → PDF (Word trên Windows) |
| `constants.py` | Mã COVA, template khách sạn/vé, bảng upload |
| `database/` | Postgres: `visa_registrations`, `han_approval_jobs` |
| `scripts/` | Chạy server nền trên VPS, watchdog |
| `tests/` | Test profile + snapshot toàn flow |

## Cấu hình

Mỗi instance dùng 1 file env (`.env`, `.env.phong`, `.env.viet`...), chọn bằng
biến `ENV_FILE` (mặc định `.env`). Các biến chính: `PORT`, `R2_*`,
`POSTGRES_*`, `DEFAULT_EMAIL`/`DEFAULT_GUID`/`DEFAULT_UID`.

Cài thư viện: `python -m pip install -r requirements.txt`
(sinh PDF cần Microsoft Word trên Windows).

## Trang nhập liệu `/web`

Thay cho việc sửa node 2 của WF-01: nhân viên đăng nhập `http://<VPS>:10000/web`,
chọn nhà, loại visa, số ngày, quan hệ (visa Q), gõ thư mục R2 rồi Gửi. Server gọi
webhook của n8n workflow **WF-00 Web Start**, workflow này gọi WF01-GENERAL như WF-01.
Tab "Chạy lại hồ sơ" thay WF-15 (xoá thư mục số hộ chiếu, khôi phục thư mục gốc từ `_archive/`).
Tab "Chạy curl": dán curl từ Telegram, sửa JSON, chạy `/run` trên đúng nhà (theo cổng).
Chọn thư mục trên máy để tải thẳng lên bucket của nhà; trang hiện tiến độ n8n và đồng hồ.

- Biến `.env` (instance 10000): `N8N_START_WEBHOOK_URL=https://<n8n>/webhook/visa-start`, `VISA_API_KEY`.
- Tài khoản: `python scripts\web_user.py add <tên> <MÃ_NHÂN_VIÊN>` (hỏi mật khẩu),
  `disable <tên>` để khoá. Mã nhân viên khớp biến Telegram trên Railway (`TELE_<MÃ>_<NHÀ>_*`).
- Mỗi người có `api_key` riêng (bảng `web_users`), trang tự gửi kèm sau khi đăng nhập.

### Lấy token trang bio (nút "🔑 Lấy token")

Khi `/run` báo lỗi token: bấm "🔑 Lấy token", chọn nhà, "Mở trang đăng nhập". Tab mới tự
điền tài khoản của nhà; người dùng làm bước xác minh rồi đăng nhập; token tự gửi về server,
được kiểm tra rồi lưu vào file token của nhà (`TOKEN_FILE_NAME`); tab bio vẫn để mở. Curl nào có
`authorization` rỗng (curl do n8n tạo) đều dùng token đã lưu này.

- Mỗi file env của nhà thêm: `BIO_LOGIN_URL` (trang đăng nhập bio), `BIO_USERNAME`, `BIO_PASSWORD`.
  Instance 10000 hỏi instance của nhà qua `127.0.0.1` (`/bio/credentials` chỉ mở cho máy VPS).
- Mỗi máy dùng trang cần cài 1 lần: tiện ích **Tampermonkey**, bật "Allow User Scripts"
  (Chrome/Edge mới), rồi mở `http://<VPS>:10000/web/visa-token.user.js` và bấm Cài đặt.
  Script chỉ chạy khi tab được mở từ nút trên `/web` (có mã phiên 15 phút), ngoài ra không làm gì.
- Code: `services/bio_token.py` (kiểm tra token, phiên, nội dung script), endpoint `/bio/*`, `/web/bio/*`.

## Chạy

**Trên máy dev:**
```powershell
$env:ENV_FILE = ".env.viet"; python server.py
```

**Trên VPS** (chạy nền, log ra file, watchdog tự khởi động lại):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_tasks.ps1 -EnvFile .env.viet [-Python "C:\...\python.exe"]
```
Tạo 2 task `VisaTool Server (<tên>)` và `VisaTool Watchdog (<tên>)`
(tên = phần sau `.env.`, file `.env` → `default`). Task chạy dưới user đang
đăng nhập (Word COM không chạy được từ nền): bật tự đăng nhập, khi rời VPS thì
đóng cửa sổ RDP, **không Sign out**. Gỡ: thêm `-Uninstall`.

Kiểm tra: `Invoke-RestMethod http://127.0.0.1:<PORT>/health`

Cập nhật code trên VPS:
```powershell
git pull
foreach ($name in "default", "phong", "viet") {
    $file = if ($name -eq "default") { ".env" } else { ".env.$name" }
    $port = (Select-String -Path $file -Pattern '^PORT\s*=\s*(\d+)').Matches.Groups[1].Value
    Stop-ScheduledTask "VisaTool Server ($name)"
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Start-Sleep 2
    Start-ScheduledTask "VisaTool Server ($name)"
}
```

## API `/run`

Body là thông tin hồ sơ (`visa_type`, `passportNumber`, `type_of_visa_sub_value`,
`entries_type`, thông tin người mời / công ty / trường...; mặc định xem
`DEFAULT_CASE` trong `main.py`). Ảnh hộ chiếu và tài liệu đầu vào lấy từ R2
theo prefix `<passportNumber>/`.

| HTTP | Nghĩa | Body |
|---|---|---|
| 200 | Thành công | `{"ok": true, "first_applyid", "record_id", "timings"}` |
| 422 | Input không hợp lệ | `{"ok": false, "step": "validate", "error"}` |
| 502 | COVA trả lỗi (HTTP hoặc `Response.Error`) | `{"ok": false, "step", "status_code", "error", "response"}` |
| 500 | Lỗi trong code / thiếu file | `{"ok": false, "step", "error"}` |

`timings` cho biết thời gian từng step (giây).

## Log (VPS)

Trong `logs/`: `server-<tên>.log` (log server), `launcher-<tên>.log`
(khởi động/thoát), `watchdog-<tên>.log` (server chậm / bị khởi động lại).
```powershell
Get-Content logs\server-viet.log -Encoding UTF8 -Tail 50 -Wait                          # xem trực tiếp
Select-String logs\server-viet.log -Encoding UTF8 -Pattern 'Flow FAILED|"level": "error"|Traceback' | Select -Last 20
Select-String logs\server-viet.log -Encoding UTF8 -Pattern '"step": "timing"|"step": "http"' | Select -Last 30
```

## Test

```powershell
python -m unittest tests.test_visa_profiles tests.test_flow_snapshots
```
`test_flow_snapshots` chạy toàn flow với COVA / R2 / Word / DB giả lập và so
mọi thứ gửi đi với `tests/snapshots/flow_snapshots.json`. Sau khi cố ý thay
đổi output: `set SNAPSHOT_UPDATE=1`, chạy lại, rồi đọc `git diff tests/snapshots`.
Snapshot có giá trị phụ thuộc ngày chạy → so sánh cùng ngày với lúc tạo baseline.

## Thêm / sửa loại visa

Xem [visa_types/README.md](visa_types/README.md): quy trình thêm loại mới,
khi step khác nhau, khi file upload khác nhau.
