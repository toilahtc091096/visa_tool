# Theo dõi cải tiến hệ thống n8n Visa

File này ghi từng thay đổi theo 3 trạng thái:

- **Ban đầu**: hệ thống đang chạy thế nào, kèm bằng chứng.
- **Kỳ vọng**: tiêu chí đo được để coi là xong.
- **Hiện tại**: kết quả thật sau khi test trên hồ sơ thật.

## Quy tắc ghi

1. **Ban đầu** chụp một lần trước khi sửa, sau đó không sửa lại. Bằng chứng ghi rõ file, workflow, node và mốc export (mục 1).
2. **Kỳ vọng** viết trước khi sửa. Mỗi tiêu chí phải trả lời được "đạt" hoặc "không đạt".
3. **Hiện tại** chỉ ghi sau khi chạy bộ hồ sơ test (mục 2). Ghi ngày, hồ sơ đã chạy và kết quả của từng tiêu chí. Không đạt thì ghi nguyên nhân rồi quay lại sửa.
4. Mỗi đợt làm 2–3 hạng mục. Chưa xong đợt trước thì chưa sang đợt sau.
5. Phạm vi miền: nâng cấp hệ thống (retry, bảo mật, hạ tầng, lưu trữ) áp dụng cả 2 miền. Chỉ thay đổi nghiệp vụ mới tách riêng miền Nam.

Trạng thái: `Chưa làm` · `Đang làm` · `Chờ test` · `Đạt` · `Không đạt` · `Bỏ`

---

## 1. Mốc export dùng làm "Ban đầu"

Nguồn: `n8n-flow/workflows/` export ngày 2026-11-20. Trước khi sửa một workflow, export lại và so `updatedAt` với bảng này. Nếu khác thì workflow đã bị sửa ngoài kế hoạch, phải so khác biệt trước.

| Workflow                        | ID               | updatedAt            | sha256 (12 ký tự) |
| ------------------------------- | ---------------- | -------------------- | ----------------- |
| WF01-GENERAL                    | C7zccdpfM4nLJmlf | 2026-11-04T02:49:01Z | a21076d11a88      |
| WF-01 phong                     | r4vVvDt56FwmflqS | 2026-11-18T08:49:17Z | 206f43a9f575      |
| WF-01 tai                       | AkNjcGjlytwjbcZx | 2026-11-18T15:08:57Z | b200e72d6988      |
| WF-01 hai                       | bUmUMb6rFmTS0ccG | 2026-10-05T16:10:54Z | cc76b500f667      |
| WF-02 PDF & Image Preprocessing | Bt8AQrVkd2IKp3yi | 2026-11-04T13:29:38Z | 1245d65578a6      |
| WF-04C Family Extractor         | ZQ9W66UJELHrlmFs | 2026-09-25T14:09:29Z | caca3ec300f0      |
| WF-04D School Processor         | zgLbsWp4suTyj8Je | 2026-11-16T07:25:33Z | 28e512c6c1bc      |
| WF-04D Special Documents        | a0y4E80S1K4C6G2C | 2026-11-17T09:59:55Z | 4a3e46916dde      |
| WF-04E Under 18                 | fFsXlOd0OtbhxhJM | 2026-11-04T13:31:49Z | c03f106b7d94      |
| WF-04F Companion                | VcrPlOGoBoRW4fdC | 2026-09-25T06:40:02Z | 67968eeaeffa      |
| WF-04G Work                     | jWF3sHSXuEiHnl9D | 2026-07-25T06:31:40Z | e677d766327d      |
| WF-04H Edu                      | zpn0b1KPRYaZgj0S | 2026-09-01T07:01:20Z | 29ac888838b9      |
| WF-04I Visit Relatives          | OF4tiRSogscqGIbi | 2026-11-18T09:14:00Z | 73f4d340b4e0      |
| WF-06 Passport                  | f11sck2DRHkfvgC4 | 2026-11-18T14:57:22Z | c2194fc687e8      |
| WF-07 Residence                 | eI1YA38wzABK7YuU | 2026-11-10T03:31:37Z | 71823d6198e4      |
| WF-07B Residence PDF Builder    | kfG0wbFqgu1l69d2 | 2026-11-13T07:11:11Z | 994f11a8cb31      |
| WF-08 Portrait                  | Aridvz5RwDbpEiFR | 2026-09-28T07:25:17Z | 4c2df11172fb      |
| WF-09 China Visa                | lY6VcyI3JRIs637I | 2026-11-18T14:57:45Z | 396e44a01ba4      |
| WF-10 Foreign Visa              | kqwZxNDonOh0ag4Z | 2026-09-25T07:49:59Z | 9c943cd68826      |
| WF-11 Blank Passport            | WsuEAHyY88thLoaj | 2026-09-25T07:50:22Z | d0bde9c6ba96      |
| WF-13 Submission                | h1RDOQmZvv0Bac1j | 2026-11-18T06:27:36Z | 3901d10997f1      |
| WF14 Clear File                 | gnqcu6RCLLvFanYw | 2026-07-14T12:29:59Z | dbfeb411633d      |
| WF-20 Notification Service      | V7kay5BbH88xyMf2 | 2026-09-25T06:44:54Z | a4758a22e13e      |
| Get Folder Name                 | 7WNUsheS0xBb00Aq | 2026-07-14T04:48:56Z | 34dc5a0cf45e      |
| WF-COMMON Merge N Images To PDF | KhwcRsV8AZ56vYg0 | 2026-11-04T07:54:56Z | 80e6c7bbcc87      |
| WF- Extracted INFO              | dx8GBdy53PZ1NnyP | 2026-11-18T14:01:22Z | ecadded1f372      |

Code Python: commit `19e4c34` trên `main`.

---

## 2. Bộ hồ sơ test cố định

Mọi đợt đều chạy lại đúng bộ này để so sánh được với nhau. Không ghi số hộ chiếu vào file này.

| Mã    | Đặc điểm cần có                                           | Bucket          | Thư mục R2 (source_prefix)         | Trạng thái            |
| ----- | --------------------------------------------------------- | --------------- | ---------------------------------- | --------------------- |
| TC-01 | Hồ sơ L15 thường: hộ chiếu, chân dung, cư trú             | `visa-data`     | `L15 - NGUYEN THI HIEN`            | Dùng                  |
| TC-02 | Hồ sơ S2                                                  | `visa-data-tai` | `Be giau-Le Thanh Hien. S2 . Khan` | Dùng                  |
| TC-03 | Hồ sơ Q2 180 ngày                                         | `visa-data-tai` | `Be giau- Lam thi cuc-Q2-180N- th` | Dùng                  |
| TC-04 | Gia đình nhiều thành viên, có con (payload dài)           | —               | —                                  | Bỏ qua, chưa có hồ sơ |
| TC-05 | Thăm thân: con rể, mời mẹ (WF-04I)                        | `visa-data-tai` | `con-re-moi-me`                    | Dùng                  |
| TC-06 | Dưới 18 tuổi, hoặc có trang hộ chiếu trắng (WF-04E/WF-11) | —               | —                                  | Bỏ qua, chưa có hồ sơ |

Tên thư mục chép đúng như nhận được, kể cả dấu cách. Nếu chưa có hồ sơ nào chứa dấu `'`, A1 sẽ được thử bằng cách sửa tạm một giá trị trong curl của TC-01.

**Chạy mốc ban đầu (làm một lần, trước khi sửa bất cứ thứ gì):** chạy 4 hồ sơ đang dùng trên workflow hiện tại. Lấy phần JSON body trong curl Telegram, lưu vào `tests/n8n-baseline/TC-0x.before.json`. Ghi thời lượng execution vào mục 3.

**Cách so kết quả:** sau mỗi đợt, lưu body mới vào `tests/n8n-baseline/TC-0x.after-<đợt>.json`, rồi so với bản `before`. Thư mục `tests/n8n-baseline/` có dữ liệu hộ chiếu nên đã được gitignore. Khác biệt nào không nằm trong phần "Kỳ vọng" của hạng mục đang làm đều tính là hỏng.

---

## 3. Chỉ số theo dõi

| Chỉ số                                                                                | Ban đầu                  | Cách đo                                                                      | Kỳ vọng sau đợt A–C                            |
| ------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| Job lỗi do AI/mạng lỗi tạm thời (429, 5xx, timeout) mỗi tuần                          | chưa đo                  | n8n → Executions, lọc Error, đếm lỗi mà nội dung có 429/5xx/timeout          | giảm rõ, mục tiêu gần 0                        |
| Curl hỏng khi chạy (dấu `'`, bị cắt)                                                  | đã xảy ra, chưa đếm      | nhân viên báo lại mỗi lần gặp                                                | 0                                              |
| Số lần phải chạy lại cả hồ sơ                                                         | chưa đo                  | ghi vào nhật ký (mục 6)                                                      | giảm                                           |
| Thời gian chạy một hồ sơ (WF-01 đến khi nhận curl)                                    | chưa đo bằng số; 2026-11-20 bạn xác nhận sau đợt A thời gian chạy không đổi đáng kể | thời lượng execution trong n8n, lấy 4 hồ sơ của mục 2 | không tăng quá 10% (retry chỉ chạy khi có lỗi) |
| Endpoint server mở ra internet không cần khoá tất cả (`server.py`, không có xác thực) | gọi thử từ máy ngoài VPS | chỉ `/health`; `/run` phải kèm khoá                                          |
| Thời gian giữ dữ liệu execution của n8n                                               | chưa biết                | xem biến `EXECUTIONS_DATA_PRUNE`, `EXECUTIONS_DATA_MAX_AGE` của n8n trên VPS | ghi lại, rồi quyết định                        |

---

## 4. Bảng tổng

| ID  | Đợt | Hạng mục                                                                              | Phạm vi                | Trạng thái | Ngày xong |
| --- | --- | ------------------------------------------------------------------------------------- | ---------------------- | ---------- | --------- |
| A1  | A   | Curl gửi qua Telegram được escape dấu `'`                                             | n8n WF-13              | Đạt        | 2026-11-20 |
| A2  | A   | Retry cho các node AI, Vision, upload R2, tạo PDF                                     | n8n (16 workflow)      | Đạt        | 2026-11-20 |
| A3  | A   | Retry và chạy tiếp khi lỗi cho `Send Curl1`, `Send Error1`                            | n8n WF-20              | Đạt        | 2026-11-20 |
| A4  | A   | Sửa node báo lỗi `Build Error Notification1` (gọi sai tên node, nên không có tin báo lỗi nào tới Telegram) | n8n WF01-GENERAL | Đạt | 2026-11-20 |
| B1  | B   | WF14 chuyển thư mục gốc vào `_archive/` thay vì xoá, Cloudflare tự xoá sau 7 ngày     | n8n WF14 + Python + R2 | Đạt | 2026-11-20 |
| B2  | B   | Quy trình chạy lại hồ sơ và workflow hỗ trợ WF-15                                     | n8n + Python           | Đạt | 2026-11-20 |
| C1  | C   | Server: mọi lời gọi từ ngoài VPS (n8n trên Railway, curl của nhân viên) phải có khoá `X-Api-Key` | Python + n8n           | Đạt | 2026-11-20 |
| C2  | C   | Token Telegram chuyển sang credential hoặc biến môi trường                            | n8n                    | Đạt | 2026-11-20 |
| C3  | C   | Tắt truy cập công khai r2.dev, bỏ `r2_public_url` khỏi trường bắt buộc                | R2 + n8n               | Đạt | 2026-11-20 |
| D1  | D   | WF-01 nhập liệu bằng Form Trigger, gộp 3 bản thành 1                                  | n8n                    | Bỏ (thay bằng trang web nhập liệu, làm sau cùng) |  |
| E1  | E   | Get Folder Name kiểm tra `ready` trước khi đổi `folder_name`                          | n8n                    | Đạt | 2026-11-20 |
| E2  | E   | WF-11 gắn cờ khi upload lỗi                                                           | n8n                    | Đạt | 2026-11-20 |
| E3  | E   | Gom code lặp (`Apply Folder Context`, hàm tìm api_port, 3 nhánh School)               | n8n                    | Bỏ | 2026-11-20 |
| E4  | E   | Tên file upload cố định cho 4 node rồi bật retry                                      | n8n WF-07B, 10, 11     | Đạt | 2026-11-20 |
| E5  | E   | Tin báo lỗi ghi rõ workflow con và node gây lỗi (hiện chỉ ghi `Call PDF & Image Preprocessing'1`) | n8n WF01-GENERAL       | Đạt | 2026-11-20 |
| W1  | W   | Trang web nhập liệu `/web` (đăng nhập, khởi chạy, chạy lại) | Python + n8n | Chờ triển khai |  |
| F1  | F   | Kịch bản dựng VPS mới nhanh và đầy đủ                                                 | hạ tầng                | Chưa làm   |           |
| G1  | —   | AI đọc cùng giấy tờ ra kết quả khác nhau (loại visa cũ, nơi cấp, ngày sinh chỉ có năm) | n8n WF-09, 04C (nghiệp vụ, cả 2 miền) | Đạt | 2026-11-20 |
| G2  | —   | Giấy 停留 (MRZ `VTCHN`) bị nhận là visa cũ thay vì giấy cư trú                          | n8n WF-04, WF-09       | Đạt | 2026-11-20 |
---

## 5. Chi tiết từng hạng mục

### A1 — Escape dấu `'` trong curl Telegram

**Ban đầu**

- WF-20 `Send Curl1` gửi `text = $json.caption`. `caption` do WF-13 `Override Visa Type1` tạo bằng `JSON.stringify(body)` và **không escape dấu `'`**.
- WF-20 `format curl1` có tạo trường `text` đã escape (`'` thành `'\''`), nhưng `Send Curl1` không dùng trường này.
- Đã xảy ra thực tế: curl bị cắt khi dữ liệu có dấu `'`.
- Nhân viên dán curl vào **Postman** (Import → Raw text). Cách escape `'\''` mà `format curl1` đang làm chỉ dùng cho bash, nên không áp dụng được.

**Cách sửa:** trong WF-13 `Override Visa Type1`, sau `JSON.stringify(body)`, thay mọi `'` bằng `'`. Đây là cách viết dấu `'` hợp lệ trong JSON: Postman và server đọc ra đúng `'`, mà chuỗi curl không còn dấu nháy đơn nào làm vỡ. Không cần sửa WF-20.

**Kỳ vọng**

- [ ] Sửa tạm một giá trị trong curl TC-01 cho có dấu `'` (ví dụ địa chỉ `O'Brien`). Import vào Postman không lỗi, và gửi đi thì server nhận đúng `O'Brien`.
- [ ] Body của TC-01, TC-02, TC-03, TC-05 (sau khi đọc thành JSON) giống hệt bản `before`.

**Hiện tại (2026-11-20):** Đạt.

- Hồ sơ thật TC-02 có `inviterDistrictPinyin = "Hua'an Xian"`.
  - Curl `before` chứa dấu `'` trần giữa body, nên lệnh bị cắt.
  - Curl `after-A` chứa `Hua'an Xian`, không còn dấu `'` trần. Đọc JSON ra vẫn đúng `Hua'an Xian`.
- Ngoài các trường do AI đọc, body của 4 hồ sơ giống bản `before` (xem A2).
- Postman: import curl TC-02 `after-A` không lỗi, body hiển thị `"Hua'an Xian"`. Python đọc JSON (cùng cách FastAPI đọc body) ra đúng `Hua'an Xian`. **Đạt.**
- Nên xem thêm: lần gửi tới, kiểm tra trường địa chỉ người mời trên bản nháp COVA hiển thị `Hua'an Xian`.

**Rủi ro:** gần như không có, vì `'` và `'` là cùng một giá trị khi đọc JSON.
**Rollback:** bỏ đoạn thay thế trong `Override Visa Type1`.

---

### A2 — Retry cho các node gọi dịch vụ ngoài

**Ban đầu:** các node sau không có retry (export 2026-11-20). Chỉ một lỗi tạm thời là cả job hỏng, chạy lại phải trả tiền AI lại từ đầu.

| Loại                      | Số node | Node                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AI đọc ảnh (gpt-4.1-mini) | 12      | 04C `Extract Family` · 04D-School `QDDH - Extract Issuing School EDU` · 04E `Analyze Payer1` · 04F `Lay Du Lieu Tu Ho Chieu1` · 04G `Lay thong tin Work` · 04H `Lay thong tin Edu` · 04I `AI OCR Inviter ID1`, `AI OCR Inviter Relative` · 06 `Build Passport Curl` · 07 `Analyze image` · 07B `Detect Document Bounds` · 09 `Extract Old China Visa1` |
| AI sửa ảnh (gpt-image-2)  | 2       | 04I `White Background1` · 08 `Edit Portrait1`                                                                                                                                                                                                                                                                                                          |
| AI xử lý text             | 6       | 04D-School `Extract School Information`, `XNH - Extract School Information1`, `XJW - Extract School Information1` · 04D-Special `Basic LLM Chain`, `Basic LLM Chain4` · INFO `Information Extractor`                                                                                                                                                   |
| Google Vision             | 3       | 04D-School `Extract School OCR`, `XNH - Extract OCR1`, `XJW - Extract OCR1`                                                                                                                                                                                                                                                                            |
| Upload R2                 | 12      | 04E `Upload under` · 04I `Upload Relationship1`, `Upload Inviter ID1`, `Upload Signature1`, `Upload Invitation Letter1`, `Upload Inviter Relative` · 06 `Upload R2 By Server` · 07B `Upload Cu Tru` · 09 `Upload China Visa1` · 10 `Upload Forgein Visa1` · 11 `Upload Blank`, `Upload Blank3`                                                         |
| Server tạo PDF            | 3       | 02 `Convert PDF To Images1` · 07B `Convert HTML String To Binary` · COMMON `Create Merged PDF1`                                                                                                                                                                                                                                                        |

**An toàn khi retry upload:** đã kiểm tra `api/r2_image.py:165-170`. Key được tạo từ `folder` và `filename`, nên retry ghi đè đúng file cũ nếu tên file cố định.

Khi retry, n8n tính lại biểu thức của node. Có 4 node đặt tên file bằng `Math.random()`: WF-07B `Upload Cu Tru`, WF-10 `Upload Forgein Visa1`, WF-11 `Upload Blank` và `Upload Blank3`. Nếu lần upload đầu thực ra đã thành công nhưng mất phản hồi (timeout), retry sẽ tạo thêm một file trùng với tên khác, và `/run` sẽ upload cả hai lên COVA. **Vì vậy 4 node này chưa bật retry.** Sẽ làm ở E4, sau khi đổi sang tên file cố định.

Các node 04I dùng `Math.random()` chỉ khi không có `working_filename` hoặc `source_filename`, nên vẫn bật retry.

**Kỳ vọng**

- [ ] Cấu hình: AI đọc ảnh, AI xử lý text, Vision, upload, tạo PDF thử tối đa 3 lần, cách nhau 3 giây. AI sửa ảnh thử tối đa 2 lần, cách nhau 5 giây.
- [ ] Chạy 6 hồ sơ của mục 2: `request_body` không đổi so với lần chạy trước.
- [ ] Thử lỗi: đặt sai API key OpenAI tạm thời, chạy 1 hồ sơ. Execution hiển thị node đã thử lại đủ số lần rồi mới báo lỗi, và lỗi được gửi lên Telegram.
- [ ] Thời gian chạy khi không có lỗi không tăng quá 10%.

**Hiện tại (2026-11-20):** Đạt.
- Thử lỗi: gắn credential sai cho WF-06 `Build Passport Curl`. Execution WF-06 lỗi sau **6,47 giây**, khớp với 3 lần thử và 2 lần chờ 3 giây. Bản cũ không có retry thì lỗi gần như ngay. Tin báo lỗi tới Telegram (sau khi sửa A4).
- Thời gian chạy khi không có lỗi: bạn xác nhận không thay đổi.
- So body 4 hồ sơ: không có khác biệt do patch (chi tiết bên dưới).

So body `before` với `after-A`, sau khi đọc thành JSON:

| Hồ sơ | Kết quả | Khác biệt |
|---|---|---|
| TC-01 | giống hệt (24 trường) | — |
| TC-02 | 1 khác biệt | `old_visaType`: `"L"` → không có |
| TC-03 | 2 khác biệt | `old_issuePlace`: `FUJIAN` → `PHUC KIEN`; `fatherBirthDate`: `1979-00-00` → `1979-01-01` |
| TC-05 | giống hệt (41 trường) | — |

Cả 3 khác biệt đều là trường do AI đọc: WF-09 `Extract Old China Visa1` và WF-04C `Extract Family`. A2 chỉ bật retry cho các node này, không đổi prompt hay code xử lý. Vì vậy đây là do AI mỗi lần đọc ra một khác, không phải do patch. Tuy nhiên đây là rủi ro nghiệp vụ, đã ghi thành G1 ở mục 5.

**Rủi ro:** retry gpt-image-2 tốn tiền, vì vậy chỉ thử 2 lần. `Edit Portrait1` đang để chạy tiếp khi lỗi, giữ nguyên cài đặt này.
**Rollback:** tắt "Retry On Fail" ở từng node.

---

### A3 — Telegram gửi curl và báo lỗi

**Ban đầu:** `Send Curl1` và `Send Error1` (WF-20) không có retry và không có cách xử lý khi lỗi. Nếu Telegram lỗi thì WF-13 lỗi và WF14 không chạy. Bốn node gửi ảnh khác đã có retry và chạy tiếp khi lỗi.

**Kỳ vọng**

- [ ] Hai node có retry 3 lần và chạy tiếp khi lỗi, giống 4 node gửi ảnh.
- [ ] TC-01 vẫn nhận được curl như cũ.

**Hiện tại (2026-11-20):** Đạt. Cả 4 hồ sơ đều nhận được curl như trước. Hai node có cùng cấu hình retry và onError với 4 node gửi ảnh đang chạy ổn. Chưa gặp lần Telegram lỗi thật nào để thấy retry chạy, nên khi gặp sẽ ghi thêm vào nhật ký.

**Rollback:** tắt retry và onError.

---

### A4 — Node báo lỗi của WF01-GENERAL bị hỏng (phát hiện khi thử retry, 2026-11-20)

**Ban đầu**
- WF01-GENERAL `Build Error Notification1` dòng 3: `const ctx = $("Validate Input").first().json;`. Trong workflow không có node tên `Validate Input`, chỉ có `Validate Input1`.
- Khi có lỗi, chính node báo lỗi này lỗi theo, với thông báo `Cannot assign to read only property 'name' of object 'Error: Referenced node doesn't exist'` (n8n 2.25.7).
- Hệ quả: lỗi ở bất kỳ đâu từ WF-02 tới WF-13, hoặc lỗi tải thư mục, đều **không có tin báo lên Telegram**. Lỗi chỉ thấy được khi mở n8n.

**Cách sửa:** đổi `$("Validate Input")` thành `$("Validate Input1")`. Chỉ sửa một dòng.

**Kỳ vọng**
- [ ] Chạy lại bài thử retry (credential sai ở WF-06 `Build Passport Curl`). Telegram nhận được tin "❌ LỖI XỬ LÝ HỒ SƠ", có Job, Folder, Visa và nội dung lỗi 401.
- [ ] Execution của WF01-GENERAL kết thúc ở `Mark Execution Failed1` với cùng nội dung lỗi.

**Hiện tại (2026-11-20):** Đạt.
- Đã sửa trực tiếp trên n8n, chạy TC-01 với credential sai. Telegram nhận được: `❌ LỖI XỬ LÝ HỒ SƠ | Job: job-hxxzb1h2 | Folder: L15 - NGUYEN THI HIEN/ | Visa: L15 | Bước: Call PDF & Image Preprocessing'1 | Lỗi: Authorization failed - please check your credentials`.
- Hạn chế còn lại: "Bước" chỉ cho biết node của WF01-GENERAL, không cho biết lỗi xảy ra ở workflow con và node nào (lần này là WF-06 `Build Passport Curl`). Ghi thành E5.
- Đã export lại WF01-GENERAL lúc 11:27. So với bản sao lưu: chỉ khác đúng dòng 3 của `Build Error Notification1`, các node và connections khác giữ nguyên.

**Rollback:** không cần, vì bản cũ vốn không chạy được.

---

### B1 — Lưu trữ thư mục gốc 7 ngày thay vì xoá ngay

**Ban đầu**

- WF14 `DELETE` gọi `POST /r2/images/delete` với `{prefix: source_prefix}` ngay sau khi WF-13 gửi curl. Đây là xoá vĩnh viễn.
- `/run` không cần thư mục gốc: nó tải thư mục theo số hộ chiếu (`utils/upload_file.py: ensure_data_folder_downloaded`). Nhưng khi curl hỏng hoặc AI đọc sai, không chạy lại n8n được vì file gốc đã mất.

**Kỳ vọng**

- [ ] Python có thêm endpoint chuyển thư mục: copy toàn bộ prefix nguồn sang prefix đích, so số file và tổng dung lượng, khớp thì mới xoá nguồn. Endpoint chỉ gọi được từ VPS (theo C1).
- [ ] WF14 chuyển `<source_prefix>` sang `_archive/<YYYY-MM-DD_HHMMSS>/<source_prefix>`. Có cả giờ trong đường dẫn để chạy nhiều lần trong ngày không ghi đè lên nhau.
- [ ] Mỗi bucket (`visa-data-phong`, `tai`, `hai`…) có quy tắc Cloudflare R2 Lifecycle: xoá object trong prefix `_archive/` sau 7 ngày.
- [ ] Chạy TC-01: thư mục gốc không còn, `_archive/<ngày>/<source_prefix>` có đủ số file như trước.
- [ ] Chuyển lỗi giữa chừng (số file không khớp) thì thư mục nguồn không bị xoá và có báo lỗi lên Telegram.

**Hiện tại (2026-11-20):** đã viết code, chờ triển khai và test.
- Python: thêm `api/r2_archive.py` và endpoint `POST /r2/folders/archive {prefix}` trong `server.py`. Endpoint copy toàn bộ sang `_archive/<YYYY-MM-DD_HHMMSS>/<prefix>`, so số file và tổng dung lượng, khớp mới xoá nguồn. Từ chối khi prefix rỗng, prefix đã nằm trong `_archive/`, hoặc thư mục đích đã có file.
- Unit test: `tests/test_r2_archive.py`, 7/7 đạt (R2 giả lập trong bộ nhớ). Đã kiểm tra thư mục có tên trùng phần đầu (`L15 - AB/` so với `L15 - A/`) không bị đụng tới.
- n8n: `n8n-flow/patched-B/WF14_-_Clear_File_gnqcu6RCLLvFanYw.json`, node `DELETE` đổi tên thành `ARCHIVE` và gọi endpoint mới. Bản gốc lưu ở `backup-2026-11-20-before-B/`.
- WF14 không bật retry, vì chuyển thư mục không chạy lại an toàn được: lần đầu đã chuyển xong mà mất phản hồi thì lần sau báo `source_not_found`. Nếu lỗi, tin báo lỗi sẽ tới Telegram (nhờ A4).

**Rủi ro:** tốn dung lượng R2 trong 7 ngày (ít). Endpoint mới thuộc nâng cấp hệ thống nên áp dụng cả 2 miền.
**Rollback:** cho WF14 gọi lại `/r2/images/delete`.

---

### B2 — Quy trình chạy lại hồ sơ

**Ban đầu:** không có quy trình. Thư mục gốc đã bị xoá nên không chạy lại được. Nếu chạy lại khi thư mục `<số hộ chiếu>/` của lần trước vẫn còn trên R2, file cũ có thể lẫn với file mới. Ví dụ: lần trước AI xếp nhầm một tài liệu vào loại X, lần sau xếp đúng loại Y, nhưng file loại X vẫn nằm đó và `/run` vẫn lấy.

**Kỳ vọng: quy trình sau khi xong B1**

| Bước | Việc                                                                                                                                                | Ai, ở đâu |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| 1    | Lấy `source_prefix` và số hộ chiếu từ tin curl Telegram của hồ sơ                                                                                   | nhân viên |
| 2    | **Xoá thư mục `<số hộ chiếu>/` trên R2** (bucket của người chạy)                                                                                    | WF-15     |
| 3    | Chuyển `_archive/<ngày>/<source_prefix>` về lại `<source_prefix>`                                                                                   | WF-15     |
| 4    | Chạy lại WF-01 với cùng cấu hình                                                                                                                    | nhân viên |
| 5    | Chạy curl mới. `/run` dùng lại bản nháp COVA cũ (`step_03_draft_person.py` tìm theo tên) và xoá các file đã upload trước khi upload lại (`step_07`) | nhân viên |

- **Nếu hồ sơ lỗi trước WF-13:** thư mục gốc chưa bị chuyển đi, nên chỉ cần làm bước 2 và 4.
- **Thư mục tạm trên máy server không cần dọn tay:** `flows/run_flow.py:272` gọi `cleanup_data_folder()` sau mỗi lần `/run`.

Tiêu chí:

- [ ] Có WF-15 "Rerun Prepare", nhập `api_port`, `source_prefix`, số hộ chiếu và `confirm`, rồi làm bước 2 và 3. Chạy tay như WF-01. Đổi sang form sẽ làm cùng D1.
- [ ] WF-15 từ chối chạy khi số hộ chiếu rỗng hoặc sai định dạng (chỉ nhận 6–12 chữ hoa và số, để không xoá nhầm thư mục khác), khi không có gì để khôi phục, và khi thư mục gốc lẫn bản lưu trữ cùng tồn tại.
- [ ] Mặc định `confirm = false` là chạy thử: chỉ báo số file sẽ xoá và sẽ khôi phục, không thay đổi gì. Phải đặt `confirm = true` mới thực hiện. Kết quả xem ở node `Ket qua` trong n8n, không gửi Telegram vì nhân viên đang chạy tay.
- [ ] Thử với TC-01: chạy lần 1, chạy lại theo quy trình. `request_body` hai lần giống nhau, COVA không sinh bản nháp thứ hai.

**Đã xác nhận (2026-11-20):** thư mục đầu ra trên R2 có tên đúng bằng số hộ chiếu.

**Hiện tại (2026-11-20):** đã viết code, chờ triển khai và test.
- Python: endpoint `POST /r2/folders/restore {prefix, passport_number, confirm}`. Tìm bản lưu trữ mới nhất của thư mục, xoá `<số hộ chiếu>/` (có dấu `/` cuối nên `C1234567/` không đụng tới `C12345678/`), rồi chuyển bản lưu trữ về chỗ cũ. Nếu thư mục gốc vẫn còn (hồ sơ lỗi trước WF-13) thì chỉ xoá thư mục đầu ra. Đã có unit test cho các trường hợp này.
- n8n: `n8n-flow/patched-B/WF-15_Rerun_Prepare.json` là workflow mới gồm 4 node: Start → `Nhap thong tin` → `Restore` → `Ket qua`. Đã chạy thử node `Ket qua` bằng Node với dữ liệu mẫu.

---

### C1 — Hạn chế truy cập server

**Ban đầu**

- `server.py` chạy trên `0.0.0.0`, không có xác thực. Ai trên internet cũng gọi được `/run`, `/r2/images/get`, `/r2/folders/download` (tải zip hộ chiếu), `/r2/images/delete`, `/agency/reassign`…
- **n8n chạy trên Railway** (xác nhận 2026-11-20), server chạy trên VPS `160.250.5.191`. n8n gọi server qua internet, IP của Railway thay đổi.
- Nhân viên chạy curl `/run` từ máy của họ, IP cũng thay đổi.
- Vì vậy không chặn theo IP được. Bản thiết kế đầu (`patched-C`, đổi sang `127.0.0.1`) đã bỏ, chưa từng được import.

**Thiết kế:** mọi lời gọi từ ngoài VPS phải kèm header `X-Api-Key`. n8n và curl của nhân viên dùng chung một khoá, lưu ở biến `VISA_API_KEY` trên Railway và trong `.env` của server. Gọi từ chính VPS (`127.0.0.1`, ví dụ script đồng bộ trạng thái) không cần khoá. `/health` mở cho tất cả.

**Kỳ vọng**

- [ ] Railway có biến `VISA_API_KEY`. `.env` của cả 3 instance có `VISA_API_KEY` cùng giá trị và `ACCESS_GUARD=log`.
- [ ] Import `patched-C2`. Chạy TC-01: hồ sơ chạy bình thường, curl trên Telegram có `-H "X-Api-Key: …"`, Postman import và gửi được.
- [ ] Chạy chế độ `log` 1–2 ngày. Log server không còn dòng `access_guard` từ n8n. Các dòng còn lại là lời gọi từ nơi khác; xem xét từng cái, cái nào hợp lệ (ví dụ link duyệt email `/han-approval/*`) thì thêm vào `ACCESS_PUBLIC_PATHS`.
- [ ] Bật `ACCESS_GUARD=enforce`. Từ máy ngoài, không có khoá: `/r2/folders/download` và `/r2/images/delete` trả 401. Có khoá: chạy bình thường. 4 hồ sơ của mục 2 chạy bình thường.

**Hiện tại (2026-11-20):** đã viết code, chờ triển khai.
- Python: `utils/access_guard.py` cùng middleware trong `server.py`. Cấu hình bằng biến môi trường:
  - `ACCESS_GUARD` = `off` (mặc định) / `log` / `enforce`
  - `VISA_API_KEY`
  - `ACCESS_PUBLIC_PATHS` (mặc định `/health`)
  - `ACCESS_KEY_PATHS` (mặc định `/`, tức mọi đường dẫn)
  - `ACCESS_LOCAL_IPS` (mặc định `127.0.0.1,::1`)
- `tests/test_access_guard.py`: 12 test. Cùng test lưu trữ là 19/19 đạt.
- n8n: `n8n-flow/patched-C2/`, 16 workflow, 23 node; bản gốc ở `backup-2026-11-20-before-C/`.
  - 20 node HTTP gọi server được thêm header `X-Api-Key = {{ $env.VISA_API_KEY }}`. IP giữ nguyên.
  - WF-03 `Match Files To Items1` (tải file bằng code) gửi kèm cùng header.
  - WF-13 `Override Visa Type1` và WF-20 `format curl1` thêm `-H "X-Api-Key: …"` vào curl.
  - Đã chạy thử bằng Node.

**Rủi ro**
- Nếu có workflow n8n khác (không nằm trong bản export) cũng gọi server, khi bật `enforce` nó sẽ bị chặn. Chế độ `log` dùng để tìm ra các workflow này trước.
- Khoá nằm trong tin curl Telegram, nên ai đọc được nhóm chat là có khoá. Chấp nhận được, vì nhóm chat vốn đã có toàn bộ dữ liệu hồ sơ.

**Rollback:** đặt `ACCESS_GUARD=off` rồi khởi động lại server. Các node n8n gửi thêm header cũng không ảnh hưởng gì khi tắt.

---

### C2 — Token Telegram ra biến Railway, gửi thêm vào nhóm của chủ

**Ban đầu**
- Token bot viết cứng trong `generate-id` của từng bản WF-01, và trong biểu thức dự phòng của WF-20 (`Send Curl1`, `Send Error1`). Chat dự phòng là `728598263`.
- Các node gửi ảnh của WF-20 dùng token của **item đầu tiên** cho cả lô.

**Mô hình (bạn xác nhận 2026-11-20)**
- Có 3 nhà: `HAI` (cổng 10000), `PHONG` (20000), `TAI` (30000).
- **Mỗi người**, cả nhân viên lẫn chủ, có **1 bot và 1 nhóm cho mỗi nhà**.
- Nhân viên S chạy hồ sơ ở nhà H: bot S-H gửi vào nhóm S-H, đồng thời bot của chủ cho nhà H gửi một bản vào nhóm của chủ cho nhà H. Mỗi nhóm nhận đủ số ảnh.

**Biến Railway**
- `TELE_PEOPLE` (vd `BAO,HANG,PHONG,ADMIN`), `TELE_HOUSES=HAI,PHONG,TAI`, `TELE_OWNER=ADMIN`
- `TELE_<NGƯỜI>_<NHÀ>_TOKEN` và `TELE_<NGƯỜI>_<NHÀ>_CHAT` cho mỗi người và mỗi nhà
- `TELE_FALLBACK_TOKEN` và `TELE_FALLBACK_CHAT` cho lỗi không xác định được ai chạy

**Cách sửa** (`n8n-flow/patched-C2C3/`, dựng trên `patched-C2` nên vẫn giữ khoá API)
- WF-01: node 2 chỉ ghi `staff` và `house`. Bỏ `chat_token`, `chat_id`, `r2_public_url`.
- WF01-GENERAL `Validate Input1`: lấy bot và nhóm của người chạy, cùng bot và nhóm của chủ cho nhà đó, từ biến Railway. Thiếu biến thì báo rõ tên biến còn thiếu. Bản WF-01 cũ (còn token và chat) vẫn chạy được: dò ra người và nhà qua token hoặc chat.
- WF-20: thêm node `Route To Groups` trước Switch, nhân mỗi tin thành bản cho nhóm người chạy và bản cho nhóm của chủ. Chủ tự chạy thì chỉ gửi 1 lần. 6 node Send dùng `tg_token` và `tg_chat` của từng tin.

**Kỳ vọng**
- [x] Chạy thử bằng Node: nhân viên ở từng nhà, WF-01 cũ, gửi curl, chủ tự chạy, lỗi không rõ người chạy, thiếu biến. Kết quả đúng bot, đúng nhóm. Không còn token, `728598263` hay r2.dev trong các node.
- [ ] Nhân viên chạy TC-01: mọi ảnh, curl và lỗi có mặt ở nhóm của nhân viên (bot của họ) và nhóm của chủ cho nhà đó (bot của chủ).

**Hiện tại:** đã sửa, chờ triển khai.

---

### C3 — r2.dev công khai

**Ban đầu:** WF01-GENERAL bắt buộc phải có `r2_public_url`, nhưng không node nào dùng giá trị này. Server không có `R2_PUBLIC_BASE` (bạn xác nhận 2026-11-20).

**Cách sửa**
- `Validate Input1` bỏ `r2_public_url` khỏi danh sách trường bắt buộc.
- WF-01 bỏ dòng `r2_public_url`.
- Trên Cloudflare, tắt Public Development URL (r2.dev) của từng bucket.

**Kỳ vọng**
- [ ] Đã tắt r2.dev trên mọi bucket. TC-01 chạy bình thường.

**Hiện tại:** đã sửa phần n8n, chờ bạn tắt r2.dev trên Cloudflare.

---

### D1 — WF-01 nhập liệu bằng form

**Ban đầu:** mỗi hồ sơ, nhân viên sửa node 2 và `generate-id` (visa_type, relation, source_prefix…) theo thông tin nhận qua Zalo, rồi chạy tay. Có 3 bản WF-01 cho 3 người. Rủi ro: quên đổi giá trị của hồ sơ trước, sửa nhầm code, hai người sửa cùng lúc.

**Kỳ vọng**

- [ ] Một WF-01 duy nhất chạy bằng Form Trigger có đăng nhập. Form có: người chạy (dropdown), visa_type (dropdown), relation (dropdown theo danh sách cho phép hiện có), source_prefix.
- [ ] Bucket, cổng, chat_id, token lấy từ bảng cấu hình theo người chạy.
- [ ] Tin Telegram đầu tiên in lại các giá trị đã nhập.
- [ ] Mỗi người chạy 1 hồ sơ: `request_body` giống cách chạy cũ.

**Hiện tại:** —

---

### E1, E2, E3

| ID  | Ban đầu                                                                                                                                                                            | Kỳ vọng                                                                             | Hiện tại |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------- |
| E1  | Get Folder Name tính `ready` và `redis_status` nhưng node `Code in JavaScript` không dùng. Khi Redis chưa có dữ liệu, `folder_name` giữ giá trị cũ (chưa xác nhận bằng hồ sơ thật) | Không có dữ liệu hộ chiếu thì gắn cờ hoặc báo lỗi, không lặng lẽ upload sai thư mục | —        |
| E2  | WF-11 `Upload Blank` và `Upload Blank3` chạy tiếp khi lỗi nhưng không gắn cờ                                                                                                       | Upload lỗi thì có cờ trong `validation` và có tin Telegram                          | —        |
| E4  | 4 node upload đặt tên file bằng `Math.random()` (07B `Upload Cu Tru`, 10 `Upload Forgein Visa1`, 11 `Upload Blank`, `Upload Blank3`), nên chưa bật retry được (xem A2)             | Tên file cố định theo thứ tự trang hoặc tên file gốc; sau đó bật retry 3 lần        | —        |
| E3  | `Apply Folder Context` lặp khoảng 9 lần; hàm tìm api_port có ở WF-13, WF-20 và WF14; WF-04D School có 3 nhánh y hệt nhau                                                           | Gom về chỗ dùng chung; `request_body` của 6 hồ sơ không đổi                         | —        |

### W1 — Trang web nhập liệu `/web` (thay node 2 của WF-01 và WF-15)

**Ban đầu:** mỗi hồ sơ, nhân viên sửa code node 2 trong WF-01 của mình (9 bản: người × nhà) rồi chạy tay. Muốn chạy lại thì sửa WF-15 bằng tay.

**Bạn chốt (2026-11-20)**
- Trang chạy trong server Python ở instance 10000.
- Mỗi người 1 tài khoản, chọn nhà trong form.
- Thư mục R2 gõ tay.
- Gửi xong chỉ báo "đã gửi", kết quả xem qua Telegram.
- Có tab chạy lại hồ sơ.
- Loại visa gồm `L, M, Q1, Q2, F, X1, X2, S2` và một ô số ngày.
- Tạm dùng HTTP trong nội bộ.

**Cách làm**
- DB: bảng `web_users` (mật khẩu băm pbkdf2, `api_key` riêng). Script `scripts/web_user.py` để thêm, khoá, mở tài khoản.
- `services/web_portal.py`:
  - Kiểm tra form: L bắt buộc 15 hoặc 30; X1 lớn hơn 180; X2 từ 1 đến 180; M và F chỉ nhận 15, 30 hoặc 90; Q1 và Q2 bắt buộc chọn quan hệ.
  - Ghép `visa_type` = mã loại + số ngày (`L30`, `Q2180`).
  - Dựng payload giống node 2 của WF-01, trong đó `staff` lấy từ tài khoản, không lấy từ trình duyệt.
  - Gọi webhook n8n kèm `VISA_API_KEY`.
  - Chạy lại: gọi `/r2/folders/restore` của instance ứng với nhà, qua `127.0.0.1`.
- `server.py`: `GET /web`, `POST /web/login` (khoá 10 phút sau 5 lần sai), `GET /web/me`, `POST /web/start`, `POST /web/rerun`. Lớp chặn truy cập mở `/web`; các thao tác tự kiểm tra khoá riêng của người dùng.
- `web/index.html`: một trang, không thư viện ngoài, dùng được trên điện thoại.
- n8n: workflow mới `WF-00 Web Start` (Webhook `POST /webhook/visa-start` → kiểm tra `X-Api-Key` → trả `{ok, job_id}` → gọi WF01-GENERAL), file ở `n8n-flow/patched-web/`.

**Kỳ vọng**
- [x] Unit test: 14 test cho form, payload, mật khẩu và endpoint. Cùng các test cũ là 34/34 đạt. Mã JavaScript của trang và của WF-00 đã chạy thử.
- [ ] Mỗi nhân viên đăng nhập, gửi 1 hồ sơ. Telegram nhận đúng như khi chạy bằng WF-01.
- [ ] Tab chạy lại: Kiểm tra rồi Thực hiện với một hồ sơ đã chạy xong.
- [ ] Sai mật khẩu 5 lần thì bị khoá 10 phút. Gọi `/web/start` mà không có khoá thì trả 401.

**Hiện tại (2026-11-20):** đã code, chờ triển khai.

---

### F1 — Dựng VPS mới

**Ban đầu:** n8n cài trực tiếp trên VPS. Server Python cài bằng `scripts/install_tasks.ps1`. Chưa có tài liệu đầy đủ để dựng VPS mới: cài n8n, Redis, Postgres, import workflow, credential, biến môi trường, Word.

**Kỳ vọng:** sẽ chi tiết sau đợt C (C1 đã đổi cách n8n gọi server). Mục tiêu là dựng xong VPS mới theo một danh sách kiểm tra mà không phải hỏi ai.

**Hiện tại:** —

---

### G1 — AI đọc cùng một giấy tờ mỗi lần ra kết quả khác (phát hiện khi test đợt A)

**Ban đầu:** chạy cùng một hồ sơ hai lần, 3/4 trường hợp các trường do AI đọc ra khác nhau:

| Hồ sơ | Trường | Lần 1 | Lần 2 | Rủi ro |
|---|---|---|---|---|
| TC-02 | `old_visaType` | `L` | không có | Có `haveChinaVisaFlag = true` mà thiếu loại visa cũ |
| TC-03 | `old_issuePlace` | `FUJIAN` | `PHUC KIEN` | Cùng một nơi cấp nhưng lúc tiếng Anh, lúc tiếng Việt không dấu |
| TC-03 | `fatherBirthDate` | `1979-00-00` | `1979-01-01` | Giấy tờ có thể chỉ ghi năm. Một lần để `00-00`, một lần tự điền `01-01` |

**Quyết định của bạn (2026-11-20), áp dụng cả 2 miền:**
1. Nơi cấp ở Trung Quốc ghi pinyin (`FUJIAN`). Nơi cấp ở Việt Nam giữ tiếng Việt (`HA NOI`, `TP HO CHI MINH`, `DA NANG`).
2. Ngày sinh chỉ có năm, hoặc ngày/tháng ghi `00`, thì điền `yyyy-01-01`.
3. Thiếu `old_visaType` thì người duyệt tự điền, không chặn hồ sơ.

**Cách sửa** (bản gốc là `n8n-flow/patched-A/`, bản đã sửa ở `n8n-flow/patched-G1/`):
- WF-09 `Extract Old China Visa1`: prompt trước đây yêu cầu AI dịch mọi nơi cấp sang tiếng Việt, đó là lý do có `PHUC KIEN`. Nay nơi cấp ở Việt Nam giữ tiếng Việt; nơi cấp ở Trung Quốc giữ pinyin như in trên visa, không dịch.
- WF-09 `Parse China Visa Result1`: thêm bảng đổi tên Hán Việt sang pinyin cho khoảng 40 tỉnh và thành phố (`PHUC KIEN` → `FUJIAN`, `QUANG CHAU` → `GUANGZHOU`…), để vẫn đúng khi AI không theo prompt. Bỏ qua các tên trùng với tỉnh Việt Nam như `HA NAM` và `SON TAY`. Giữ mặc định `HA NOI` khi trống, đúng như yêu cầu trước đây.
- WF-04C `normal date`: ngày hoặc tháng `00` thì đổi thành `01`.

**Kỳ vọng**
- [ ] Đã chạy thử code bằng Node: `PHUC KIEN`, `Phúc Kiến`, `FUJIAN` → `FUJIAN`; `Quảng Châu` → `GUANGZHOU`; `HA NOI`, `TP HO CHI MINH`, `DA NANG` giữ nguyên; `00/00/1979`, `1979-00-00`, `1979` → `1979-01-01`; `05/03/1979` → `1979-03-05`.
- [ ] Chạy TC-03 hai lần: `old_issuePlace = FUJIAN` cả hai lần, `fatherBirthDate = 1979-01-01` cả hai lần.
- [ ] Chạy TC-02: `old_issuePlace = TP HO CHI MINH` giữ nguyên.
- [ ] TC-01 và TC-05: body giống bản `before`, trừ các trường AI đọc.

**Hiện tại (2026-11-20):** đã sửa, đã chạy thử code bằng Node (tiêu chí đầu đạt), chờ import và chạy hồ sơ thật. Chỉ 3 node trên bị đổi, connections giữ nguyên.

---

### G2 — Giấy 停留 bị nhận là visa cũ (phát hiện khi test G1, 2026-11-20)

**Ban đầu**
- Hồ sơ có 2 tem: một visa L thật (MRZ `VLCHN…`, cấp tại 胡志明市 năm 2025) và một giấy **停留** (gia hạn lưu trú, cấp tại 福建 ngày 2026-08-11, số đỏ 101816009, MRZ `VTCHN…`).
- Giấy 停留 có tiêu đề "中华人民共和国签证 / VISA", nên AI xếp vào `china_visa`. `Validate Classification` của WF-04 chỉ nhận `R<CHN` là giấy cư trú, còn mọi MRZ bắt đầu bằng `V` có `CHN` thì ép thành visa.
- Hệ quả: giấy 停留 thành "visa cũ" và được chọn vì có ngày cấp mới nhất. Telegram báo "ẢNH HỘ CHIẾU TRUNG QUỐC CŨ", nơi cấp ra `FUJIAN`. Theo quy ước, giấy này là giấy cư trú, chỉ dùng khi không có visa cũ.
- Logic giấy cư trú vẫn còn đầy đủ: WF-04 phân loại, WF-05 chuyển sang WF-09, WF-09 tách prompt và parse, `Pick Latest China Visa` ưu tiên visa và chỉ gắn thêm cờ giấy cư trú, WF-12 và Python xử lý tiếp. Chỉ có bước nhận diện giấy 停留 bị thiếu.

**Cách sửa** (`n8n-flow/patched-G2/`)
- WF-04 `Validate Classification`: MRZ bắt đầu bằng `VT` và có `CHN` thì luôn là `china_residence_permit`. Kiểm tra này chạy trước nhánh `V` → visa.
- WF-04 `Build Classification Prompt`: STEP 0 thêm mô tả giấy 停留 (MRZ `VT…`, dải loại ghi 停留, các ô Entries/Valid for Entry/Duration là N/A, ghi chú "Permitted to stay until").
- WF-09 `Extract Old China Visa1`: prompt giấy cư trú nói rõ có cả giấy 停留; `validUntil` lấy từ ghi chú "本次允许停留至…". File WF-09 này đã gồm cả phần sửa của G1.

**Kỳ vọng**
- [x] Chạy thử bằng Node: `VTCHN…` (AI nói visa hoặc unknown) → `china_residence_permit`; `VLCHN…`, `V<CHN` → `china_visa` như cũ; `R<CHN` → giấy cư trú; `P<VNM` → hộ chiếu; `VTKOR` không bị đổi.
- [ ] Chạy lại hồ sơ này: Telegram báo "ẢNH GIẤY CƯ TRÚ TRUNG QUỐC" cho giấy 停留, số 101816009. Visa cũ là L, số M7355333, nơi cấp `TP HO CHI MINH`, ngày cấp 2025-01-15.

**Hiện tại:** —

---

## 6. Nhật ký

| Ngày       | ID    | Việc                                                                                                                                                                                                                                                                                                             | Hồ sơ test | Kết quả            | Ghi chú                                            |
| ---------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------ | -------------------------------------------------- |
| 2026-11-20 | —     | Chụp mốc ban đầu (mục 1), lập file theo dõi                                                                                                                                                                                                                                                                      | —          | —                  |                                                    |
| 2026-11-20 | A1–A3 | Sửa trên export 09:04 (bạn xác nhận là bản mới nhất): 37 thay đổi trong 18 workflow. Bản gốc lưu ở `n8n-flow/backup-2026-11-20-before-A/`, bản đã sửa ở `n8n-flow/patched-A/`. Đã kiểm tra: chỉ các node trong danh sách bị đổi, connections giữ nguyên; code A1 chạy thử bằng Node, dữ liệu có `'` đọc lại khớp | chưa       | Chờ import và test | 4 node upload tên ngẫu nhiên chuyển sang E4        |
| 2026-11-20 | —     | Chốt bộ hồ sơ test: TC-01, 02, 03, 05. TC-04 và TC-06 bỏ qua vì chưa có hồ sơ                                                                                                                                                                                                                                    | —          | —                  | A1 đổi cách sửa sang `'` vì nhân viên dùng Postman |
| 2026-11-20 | A1–A3 | Đã import `patched-A`, chạy 4 hồ sơ trước và sau, so body | TC-01, 02, 03, 05 | A1 gần đạt; A2, A3 không thấy lỗi do patch | TC-02 có `Hua'an Xian` thật. Có 3 khác biệt do AI, ghi thành G1. Còn chờ: thử Postman, thử API key sai, thời gian chạy |
| 2026-11-20 | A2, A4 | Thử retry: gắn credential sai cho WF-06 `Build Passport Curl` | TC-01 | Lỗi đi tới WF01-GENERAL, nhưng `Build Error Notification1` hỏng | Phát hiện A4: gọi `$("Validate Input")` trong khi node tên `Validate Input1`, nên không có tin báo lỗi Telegram |
| 2026-11-20 | A4 | Sửa `$("Validate Input1")` trực tiếp trên n8n, chạy lại bài thử | TC-01 | Đạt: Telegram nhận được tin lỗi | Tin chưa ghi node gây lỗi → E5 |
| 2026-11-20 | A2, A3 | Đo retry: WF-06 lỗi sau 6,47 giây. Thời gian chạy bình thường không đổi | TC-01 | **Đạt. Đóng đợt A** (A1–A4) | Còn lại G1 chờ bạn quyết định nghiệp vụ |
| 2026-11-20 | G1 | Bạn quyết định: `old_issuePlace` dùng dạng `FUJIAN`; ngày sinh chỉ có năm điền `yyyy-01-01`; thiếu `old_visaType` thì người duyệt tự điền | — | — | Chưa sửa |
| 2026-11-20 | B1, B2 | Viết `api/r2_archive.py`, 2 endpoint, `tests/test_r2_archive.py` (7/7 đạt), `patched-B/` (WF14 sửa, WF-15 mới) | — | Chờ triển khai | Thứ tự triển khai: Python → quy tắc Lifecycle → import n8n |
| 2026-11-20 | G1 | Sửa WF-09 (prompt và bảng đổi tên nơi cấp) và WF-04C (ngày `00`) trên bản `patched-A`. Kết quả ở `patched-G1/` | — | Đã chạy thử bằng Node, chờ hồ sơ thật | Bạn quyết định áp dụng cả 2 miền |
| 2026-11-20 | G1, G2 | Bạn chạy G1: nơi cấp ra `FUJIAN`, đúng định dạng. Phát hiện G2: giấy 停留 bị nhận là visa cũ. Sửa WF-04 và WF-09, kết quả ở `patched-G2/` | hồ sơ có giấy 停留 | G1 đúng định dạng; G2 chờ test | WF-09 dùng bản trong `patched-G2/`, không dùng `patched-G1/` |
| 2026-11-20 | A, B, G1, G2 | Kiểm tra bản export 12:39: đủ các bản sửa A, B (gồm WF-15 mới), G1, G2 | — | Đã import | Bản export không có WF-01 phong và tai |
| 2026-11-20 | C1 | Viết `utils/access_guard.py` cùng middleware (10 test), `patched-C/` (23 node) | — | Chờ triển khai | Triển khai theo thứ tự: Python (mặc định off) → biến môi trường n8n và import → `log` → đọc log → `enforce` |
| 2026-11-20 | B1, B2, G1, G2 | Bạn triển khai và test | TC-03, hồ sơ có giấy 停留 | **Đạt** | Bạn báo "kết quả ok hết" |
| 2026-11-20 | C1 | Phát hiện n8n chạy trên Railway, không cùng VPS với server, nên cách chặn theo `127.0.0.1` không dùng được | — | **Không import `patched-C/`** | Thiết kế lại: n8n gửi `X-Api-Key` cho mọi lời gọi server |
| 2026-11-20 | C1 | Thiết kế lại cho Railway: dùng khoá `VISA_API_KEY` cho mọi lời gọi từ ngoài. Python 12 test; `patched-C2/` (23 node). Đã xoá `patched-C` | — | Chờ triển khai | Railway đã có `N8N_ENCRYPTION_KEY` và cho phép đọc biến môi trường, bạn đã restart thử thành công |
| 2026-11-20 | C2, C3 | Token Telegram chuyển ra biến Railway; mỗi tin gửi cả nhóm nhân viên và nhóm nhà của chủ; bỏ bắt buộc `r2_public_url`. Kết quả `patched-C2C3/` (dựng trên `patched-C2`) | — | Chờ triển khai | D1 bỏ, vì sẽ làm trang web nhập liệu sau cùng |
| 2026-11-20 | C2 | Làm lại theo mô hình mỗi người 1 bot và 1 nhóm cho mỗi nhà (HAI 10000, PHONG 20000, TAI 30000); bản sao cho chủ gửi bằng bot của chủ cho nhà đó | — | Chờ triển khai | Thay bản `patched-C2C3` trước, bản đó dựng theo kiểu bot theo nhà |
| 2026-11-20 | C2 | Đổi 10 bản WF-01 (BAO, HANG, LONG mỗi người 3 nhà, chưa có BAO-TAI; ADMIN nhà PHONG và TAI) sang `staff` và `house`; dò người và nhà theo bot trước, theo chat sau (chat của mỗi người giống nhau ở cả 3 nhà). Kết quả `patched-WF01/` (12 file), bản gốc ở `backup-2026-11-20-before-WF01/` | — | Chờ import | Danh sách biến điền sẵn ở `n8n-flow/railway-tele-vars.txt` (có token, xoá sau khi dán) |
| 2026-11-20 | C1, C2, C3 | Bạn đã import, bật `ACCESS_GUARD=enforce`, tắt r2.dev, kiểm tra Telegram | — | **Đạt. Đóng đợt C** | |
| 2026-11-20 | E1, E2, E4, E5 | Sửa trên export 15:31. Kết quả `patched-E/` (5 workflow, 6 node), bản gốc ở `backup-2026-11-20-before-E/`. **E5:** tin lỗi có link tới execution (biến `N8N_EDITOR_BASE_URL` hoặc `WEBHOOK_URL`, không có thì ghi Execution ID). **E1:** Get Folder Name dừng và báo rõ khi chưa có thư mục hộ chiếu, thay vì upload sai chỗ. **E4:** tên file cố định theo `document_id` (hoặc job và vị trí item) cho 4 node upload, rồi bật retry 3 lần. **E2:** WF-11 bỏ chế độ chạy tiếp khi lỗi, upload lỗi sau 3 lần thử thì dừng và báo lỗi | — | Chờ test | Đã chạy thử bằng Node: tên file giữ nguyên khi retry, link execution đúng, E1 báo lỗi khi thiếu Redis |
| 2026-11-20 | C2 (sửa lỗi) | Bạn báo: nhóm admin không nhận được curl (ảnh thì có). Nguyên nhân: WF-20 `format curl1` chỉ xử lý `$input.first()` và trả về 1 item, nên bản cho admin từ `Route To Groups` bị bỏ. Sửa thành xử lý mọi item. Kết quả `patched-curl-fix/` | Node: 2 item vào, ra 2 tin curl | Chờ import | Các node khác của WF-20 giữ nguyên |
| 2026-11-20 | E1, E2, E4, E5 | Bạn đã import `patched-E` và `patched-curl-fix`, test xong | — | **Đạt. Đóng đợt E** | |
| 2026-11-20 | E3 | Bỏ. Cụm `Has Folder Context?` + `Apply Folder Context` (7 chỗ trong WF-04E, WF-04I, WF-COMMON Merge) là tối ưu có chủ ý (PERF-D): WF-04 đọc Redis một lần rồi gắn sẵn `folder_ctx`, nên không phải gọi `Get Folder Name` kèm ảnh. Gom về một workflow con sẽ làm mất tối ưu này. Các chỗ lặp còn lại (XNH/XJW, `getText`, `safeParse`…) lợi ích nhỏ, n8n không cho dùng chung code | — | Bỏ | Không đề xuất lại |
| 2026-11-20 | W1 | Code trang `/web`: bảng `web_users`, `services/web_portal.py`, 5 endpoint, `web/index.html`, `scripts/web_user.py`, WF-00 Web Start (`n8n-flow/patched-web/`). 34/34 test đạt | — | Chờ triển khai | F1 để sau cùng |
