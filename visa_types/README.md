# Thêm / sửa loại visa

Mỗi loại visa là **một class `VisaProfile`** được đăng ký bằng `@register`
(xem `base.py`). Luồng chung trong `flows/flow_step/` chỉ gọi `ctx.profile`,
nên mọi khác biệt giữa các loại visa phải nằm trong profile, không viết
`if visa_type == ...` trong `flows/`.

```
visa_types/
  base.py       VisaProfile (mặc định + hook), registry, normalize_visa_type
  documents.py  các loại giấy tờ sinh ra (DocumentStep)
  tourism.py    L15, L30      business.py  M
  family.py     Q1, Q2        study.py     F
```

---

## A. Quy trình thêm một loại visa mới

Ví dụ thêm `X1`. Làm theo thứ tự, bước nào không áp dụng thì bỏ qua.

### 1. Thu thập thông tin từ COVA (làm tay 1 lần trên web)
Khai thử 1 hồ sơ loại X1 trên web COVA, mở DevTools (F12) → tab Network:
- `SaveApplyInfo` → lấy `visaType`, `visaPurpose` của từng sub-type.
- `SaveUploadAccessory` (mỗi lần upload) → lấy `categoryCode` + `materialCode`
  của từng ô upload.
- So sánh body các API `Save*Info` với loại gần giống nhất (L/M/Q/F) để biết
  step nào khác.

### 2. Khai báo mã trong `constants.py`
| Hằng số | Khoá | Nội dung |
|---|---|---|
| `SERVICE_VISA_TYPE` | `service_key` (vd `"X1"`) | tập sub-type hợp lệ |
| `VISA_TYPE_VALUE` | `service_key` | sub-type → `{"visaPurpose": ..., "visaType": ...}` |
| `APPLY_VISA_VALIDITY` | `service_key` | số tháng hiệu lực mặc định |
| `WEEK_SKIP_BY_TYPE` | `code` | số tuần lùi ngày đi (khi không có ngày trong request) |
| `UPLOAD_CONFIG`, `UPLOAD_FILE_CODE_BY_VISA_TYPE` | `code` | xem mục C |
| `FLIGHT_TEMPLATE` | `code` | chỉ khi cần sinh vé máy bay |

### 3. Cho `normalize_visa_type` hiểu mã mới (`base.py`)
Hàm này tách giá trị `visa_type` trong request thành `(code, duration)`.
`duration` được gửi lên COVA làm `applyMaxStayDays`
(`last_letter_visa_type = visa_duration or visa_type[1:]`).
Mã lạ như `"S1"` hiện ra `("S1", "")` → `applyMaxStayDays = "1"` (**sai**).
Thêm nhánh cho tiền tố mới, vd:
```python
if raw_type.startswith("X"):
    return "X1", raw_duration or "30"
```

### 4. Tạo profile
Tạo `visa_types/<ten>.py` (hoặc thêm vào file của họ visa gần nhất):
```python
from .base import VisaProfile, register
from .documents import VisaCenterConfirmation

@register
class X1Visa(VisaProfile):
    code = "X1"                 # = visa_type sau normalize, = khoá bảng upload
    service_key = "X1"          # khoá trong SERVICE_VISA_TYPE / VISA_TYPE_VALUE
    documents = (VisaCenterConfirmation(),)
    accepts_requested_dates = True

    def build_travel_json(self, travel):
        ...                     # bắt buộc: body SaveTravelInfo
```
Nếu giống 1 loại có sẵn → **kế thừa** loại đó và chỉ ghi phần khác
(vd `class X1Visa(FamilyVisa)` thì dùng lại travel info kiểu Q).
Class chỉ để dùng chung (như `FamilyVisa`, `TourismVisa`) thì **không** `@register`.

### 5. Import module trong `visa_types/__init__.py`
```python
from . import business, family, study, tourism, ten_moi  # noqa: E402,F401
```
Không import → `@register` không chạy → request báo `visa_type not supported`.

### 6. Field mới trong request `/run` (nếu có)
Hiện field phải được nối qua 4 chỗ (sẽ gọn lại khi làm `FlowInput`):
1. `main.py` → `DEFAULT_CASE` (giá trị mặc định)
2. `main.py` → lời gọi `run_flow(...)` trong `main()` (truyền `data["field"]`)
3. `flows/run_flow.py` → tham số của `run_flow(...)`
4. `flows/run_flow.py` → lời gọi `build_flow_context(..., field=field)`

Sau đó dùng được `ctx.field` trong profile / document.

### 7. Test
1. `tests/test_visa_profiles.py` → thêm `"X1"` vào danh sách
   `test_expected_types_are_registered`.
2. `tests/test_flow_snapshots.py` → thêm 1 case vào `CASES`
   (thêm case biến thể nếu có: reuse, dưới 18 tuổi...).
3. Chạy **so sánh trước** để chắc các loại cũ không đổi:
   `python -m unittest tests.test_visa_profiles tests.test_flow_snapshots`
   → chỉ case mới báo thiếu là đúng.
4. Ghi snapshot: `set SNAPSHOT_UPDATE=1` rồi chạy lại, **`git diff
   tests/snapshots` chỉ được có case mới**. Đọc snapshot của case mới để kiểm
   tra body gửi COVA có đúng như bước 1 không.

### 8. Chạy thử thật 1 hồ sơ, rồi merge + deploy.

---

## B. Khi một step của loại mới KHÁC các loại hiện có

Quy tắc: **khác biệt đi vào profile, luồng chung giữ nguyên.**

### B1. Khác biệt đã có "nút" sẵn → chỉ cấu hình
| Muốn | Làm trong profile |
|---|---|
| Nhận ngày đi/về từ request (`arrivalDate`/`departureDate`) | `accepts_requested_dates = True` |
| Công việc cố định (vd "Student") | `job_type_label = "Student"` |
| Công việc = công ty trong request (`companyNameVi`...) | `works_at_inviting_company = True` |
| Người liên hệ khẩn cấp = giám đốc công ty | `manager_is_emergency_contact = True` |
| Luôn tự chi trả chuyến đi | `always_self_paid = True` |
| Xoá `chung/*` local trước khi sinh giấy tờ | `cleans_local_common_docs = True` |
| Tải thư mục đầu vào riêng từ R2 (step 2, 7) | viết `prepare_resources(self, ctx)` |
| Random khách sạn | viết `choose_hotel(self, ctx)` |
| Body SaveTravelInfo | viết `build_travel_json(self, travel)` |
| Dùng lại giấy tờ từ passport khác | `reuse = ReuseRule(source_field, folders, missing_message)` |

### B2. Giấy tờ sinh ra khác → sửa `documents`
- Bớt / thêm / đổi thứ tự: sửa tuple `documents = (...)`.
- Giấy tờ **mới**: trong `documents.py` tạo class kế thừa `DocumentStep`,
  đặt `output_folder`, viết `async def render(self, ctx)` (template `.docx`
  để trong `resources/`, hàm render đặt trong `generate_file/`).
  Muốn upload nó lên COVA → thêm `output_folder` vào `UPLOAD_CONFIG` (mục C).
- Giấy tờ cũ nhưng cần tham số khác → thêm tham số vào `__init__`
  (như `InvitationLetter(output_folder)`, `FlightTicket(three_cities=True)`).

### B3. Step khác nhưng CHƯA có hook → thêm hook mới
Ví dụ loại X1 cần body `SaveEducationInfo` khác:
1. Trong `VisaProfile` (`base.py`) thêm hook với **mặc định = hành vi hiện tại**:
   ```python
   def education_overrides(self, ctx, body) -> None:
       """Chỉnh body SaveEducationInfo; mặc định không đổi gì."""
   ```
2. Trong step tương ứng (`step_05_...py`) gọi hook ngay trước khi gửi:
   `ctx.profile.education_overrides(ctx, body_save_education_info)`
3. Override hook trong `X1Visa`.
4. Chạy snapshot test: **các loại cũ phải không đổi** (vì mặc định giữ nguyên).

Cùng cách đó cho: bỏ qua 1 API (hook trả `bool`), gọi thêm API
(`async def after_travel_info(self, ctx, client) -> bool: return True`)...
Không thêm `if ctx.visa_type == ...` vào `flows/`.

### B4. Kiểm tra các renderer có đoán theo visa type
Một số renderer trong `generate_file/` còn tự rẽ nhánh theo payload:
`cv_info` (Q1 → `visa_type_number = "000"`), `flight_info` (L30 → ngày về
2W6D), `thumoi_info` (Q1/Q2 → ô tick). Loại mới dùng các giấy tờ này thì
kiểm tra kết quả render.

---

## C. Khi file upload KHÁC

Upload (step 7) do 2 bảng trong `constants.py` quyết định, khoá = `profile.code`:

| Bảng | Nghĩa |
|---|---|
| `UPLOAD_FILE_CODE_BY_VISA_TYPE[code][group][doc_type]` | **Các ô upload trên COVA**: list `{categoryCode, materialCode}` |
| `UPLOAD_CONFIG[code][doc_type]` | **Lấy file ở đâu**: `{"folder", "limit"}` hoặc list nhiều nguồn |

`profile.upload_plan()` ghép 2 bảng theo `doc_type`, rồi lấy file lần lượt từ
các `folder` và **ghép theo thứ tự** với các ô COVA:

```python
UPLOAD_FILE_CODE_BY_VISA_TYPE["X1"] = {
    "COMMON": {
        "OTHER_MATERIALS": [                                   # 3 ô trên COVA
            {"categoryCode": "...", "materialCode": "mfa-099_1"},
            {"categoryCode": "...", "materialCode": "mfa-099_2"},
            {"categoryCode": "...", "materialCode": "mfa-099_3"},
        ],
    },
}
UPLOAD_CONFIG["X1"] = {
    "OTHER_MATERIALS": [
        {"folder": L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH, "limit": 1},  # → ô 1
        {"folder": "x1\\tai-lieu-khac", "limit": 2},                        # → ô 2, 3
    ],
}
```

Quy tắc:
- **Mỗi `doc_type` trong `UPLOAD_CONFIG` phải có mã trong
  `UPLOAD_FILE_CODE_BY_VISA_TYPE`**, nếu không file bị bỏ qua âm thầm
  (lỗi F thiếu visa cũ lần trước). `tests/test_visa_profiles.py` kiểm tra điều này.
- Ngược lại, có mã mà không có config thì ô đó để trống (hợp lệ).
- Số file upload tối đa = số ô COVA; `limit` lớn hơn cũng không upload thêm.
- `folder` là đường dẫn tương đối, tìm lần lượt trong
  `resources/data_<passport>/` (tải từ R2 `<passport>/...`) rồi `resources/`
  (vd `doanh-nghiep/`, `du-hoc/` do `prepare_resources` tải về).
  Giấy tờ do tool sinh ra nằm ở `output_folder` của DocumentStep tương ứng.
- Upload lỗi (HTTP hoặc `Response.Error`) sẽ **dừng flow**, nên chỉ khai báo
  những ô thực sự có trên form COVA của loại đó.
- Tên `doc_type` cũng là giá trị client gửi trong `upload_config_keys` khi
  `is_update_info = true` (chỉ upload lại các mục đó).
- Hai loại dùng chung bảng → gán alias: `UPLOAD_CONFIG["M"] = UPLOAD_CONFIG["M90"]`.
- Loại có cách upload khác hẳn (hiếm) → override `upload_plan()` trong profile.

---

## Checklist nhanh

- [ ] Mã COVA (visaType/visaPurpose, ô upload) đã lấy từ DevTools
- [ ] `constants.py`: SERVICE_VISA_TYPE, VISA_TYPE_VALUE, APPLY_VISA_VALIDITY, WEEK_SKIP_BY_TYPE, 2 bảng upload
- [ ] `normalize_visa_type` trả đúng `(code, duration)`
- [ ] Profile có `@register`, `code`, `service_key`, `documents`, `build_travel_json`
- [ ] Module được import trong `visa_types/__init__.py`
- [ ] Field mới (nếu có) nối qua main.py + run_flow.py
- [ ] Test profile + snapshot pass, snapshot cũ không đổi
- [ ] Chạy thử 1 hồ sơ thật → merge → deploy
