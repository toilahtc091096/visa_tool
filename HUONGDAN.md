# HUONGDAN.md — Hướng dẫn chuẩn bị file hồ sơ (cho Claude session sau)

Tài liệu này gom **mọi thứ đã biết** về phần "Hướng dẫn file" của trang web khai hồ sơ:
quy tắc đặt tên file theo từng loại visa (nghiệp vụ), code nằm ở đâu, cách sửa và kiểm tra,
và các quyết định người dùng đã chốt. Đọc hết trước khi sửa nội dung hướng dẫn.

> Nguồn sự thật của nội dung là `web/guide.js`. Tài liệu này mô tả lại; nếu lệch nhau thì
> code đúng, và cập nhật lại file này.

---

## 1. Tổng quan

- Nhân viên khai hồ sơ ở trang `/web` (form "Khởi chạy hồ sơ"): chọn **Nhà**, kéo **thư mục hồ sơ**
  từ máy vào, chọn **loại visa**, bấm Gửi. Thư mục được tải lên R2 của nhà; n8n đọc file theo **tên file**
  để biết là giấy gì.
- Vì vậy cần hướng dẫn nhân viên **chuẩn bị thư mục và đặt tên file** đúng. Hướng dẫn có 2 chỗ xem,
  cùng một nội dung:
  1. **Popup** "ⓘ Hướng dẫn file" cạnh ô "Loại visa" trong form `/web` (rộng 60% trang).
  2. **Trang riêng** `/web/huong-dan` (công khai, không cần đăng nhập). Popup có nút "↗ Trang riêng";
     thanh trên cùng của `/web` có link "📘 Hướng dẫn". Cả hai mở đúng visa/nhà/lựa chọn đang chọn.
- Hướng dẫn **chỉ là tài liệu**: các lựa chọn trong hướng dẫn (Cá nhân/Gia đình, Người đầu/sau, Dưới 18…)
  **không** thêm ô nào vào form và **không** gửi gì lên curl. (Người dùng đã xác nhận.)

### Nhà và miền

| Nhà   | Miền | Cổng instance | Ghi chú cho hướng dẫn                                     |
| ----- | ---- | ------------- | --------------------------------------------------------- |
| HAI   | Bắc  | 10000         | cần 2 trang trắng hộ chiếu; giới hạn số file `qmoi`/`qcm` |
| PHONG | Bắc  | 20000         | như HAI                                                   |
| TAI   | Nam  | 30000         | không cần trang trắng; gộp mọi file cùng loại thành 1 PDF |

Trong code: `NORTH_HOUSES = ['HAI', 'PHONG']` (web/guide.js); danh sách nhà thật ở
`services/web_portal.py` → `HOUSES`.

---

## 2. Quy tắc đặt tên chung (áp dụng mọi loại visa)

Có **2 loại tên file** — đây là quy tắc quan trọng nhất:

| Loại file                                                                                                                                                               | Cách đặt tên                                                                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **File cơ bản**: hộ chiếu, ảnh thẻ, trang trắng hộ chiếu, CT07 / xác nhận cư trú, visa TQ cũ                                                                            | **Giữ tên gốc, không cần đổi** — AI tự đọc ra là giấy gì. Chỉ cần tên là chữ không dấu, số, `_`, `-` (a-z A-Z 0-9 \_ -). Ví dụ hợp lệ: `IMG_2041.jpg`, `scan-01.png`, `ct07.pdf`. |
| **File có tiền tố cố định**: người thân cắt từ hộ khẩu (`tt_`…), người đi cùng (`cv_`), dưới 18 (`duoi18_`), giấy riêng của từng loại visa (`thumoi`, `qmoi_`, `scm_`…) | **Đổi về đúng tên như hướng dẫn** — hệ thống nhận diện theo tên/tiền tố.                                                                                                          |

- Tên có dấu cách hoặc dấu tiếng Việt → đổi sang không dấu, không cách.
- Đuôi file giữ nguyên (.jpg, .png, .pdf).
- Giấy nhiều trang/nhiều tờ: tăng số cuối `_1`, `_2`… theo đúng thứ tự trang.
- Không có giấy nào thì bỏ qua, **không tạo file trống**.
- Mỗi hồ sơ là 1 thư mục, tên kiểu `L30 - NGUYEN VAN A`, `M - NGUYEN VAN A`, `Q2 - NGUYEN VAN A`.

### File cơ bản (mọi loại visa)

| Giấy                                                                         | Bắt buộc?                                                     |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Trang thông tin hộ chiếu (thẳng, đủ 4 góc, rõ dòng mã chân trang, không loá) | bắt buộc                                                      |
| Ảnh thẻ 4x6 nền trắng (mới, nhìn thẳng, không kính)                          | bắt buộc                                                      |
| Trang trắng hộ chiếu (2 trang)                                               | **bắt buộc với nhà HAI, PHONG (miền Bắc)**; nhà TAI không cần |
| Xác nhận cư trú CT07 / xác nhận việc làm                                     | nếu có                                                        |
| Visa Trung Quốc cũ (mỗi visa 1 file)                                         | nếu có                                                        |

### Hộ khẩu / giấy có nhiều người → cắt từng người (mọi loại, nếu có)

Ảnh hộ khẩu / xác nhận cư trú thường có nhiều người trên 1 trang. **Cắt mỗi người thân 1 file và đặt
đúng tên**, tên theo quan hệ **với người xin visa** (không theo chủ hộ):

| Tên file          | Là ai (so với người xin visa) |
| ----------------- | ----------------------------- |
| `tt_cha`          | bố                            |
| `tt_me`           | mẹ                            |
| `vo_chong`        | vợ hoặc chồng                 |
| `con_1`           | con thứ nhất (lớn nhất)       |
| `con_2`, `con_3`… | con tiếp theo theo tuổi       |

- Cắt đủ khung người đó (ảnh nếu có, họ tên, ngày sinh, quan hệ). Phần của chính người xin visa không cần cắt.
- Cắt xong **bỏ ảnh gốc** khỏi thư mục (tránh tải trùng).
- Một người có 2 ảnh: `tt_cha_1`, `tt_cha_2`.
- Người dùng xác nhận: `tt_cha`, `tt_me`… **vẫn cần** và phải **đúng tên**.

### Người đi cùng `cv_` (L gia đình, M, F, X1, X2)

Mỗi người đi cùng 1 file **trang thông tin hộ chiếu**, tên bắt buộc `cv_1`, `cv_2`…
(vd đi cùng bố mẹ: `cv_1` = bố, `cv_2` = mẹ). n8n WF-04 nhận là `companion_passport`.
Sai kiểu `cv1.jpg`, `nguoi di cung.jpg` → hệ thống không nhận ra.

### Người xin visa dưới 18 tuổi `duoi18_` (L, Q1, Q2, S2 khi chọn "Dưới 18")

| Tên file     | Là gì                                   |
| ------------ | --------------------------------------- |
| `duoi18_ks`  | giấy khai sinh của người xin visa       |
| `duoi18_dc1` | thông tin người đi cùng thứ 1 (vd bố)   |
| `duoi18_dc2` | thông tin người đi cùng thứ 2 (vd mẹ)   |
| `duoi18_pay` | thông tin người sẽ thanh toán chuyến đi |

**Chỉ đi cùng 1 người**: thay 1 trong 2 file `duoi18_dc` bằng **giấy uỷ quyền của người còn lại**
(vd đi cùng bố: `duoi18_dc1` = thông tin bố, `duoi18_dc2` = giấy uỷ quyền của mẹ).

---

## 3. Theo từng loại visa

Mỗi loại (trừ L) có mục **"2. Thứ tự làm file"** đứng thứ 2 (sau sơ đồ thư mục), mở sẵn.

### L — du lịch

Lựa chọn trong hướng dẫn: **Hồ sơ** Cá nhân / Gia đình → nếu Gia đình: **Người đầu / Người sau**
(hiện tại 2 trường hợp chuẩn bị giống nhau) · **Tuổi** Từ 18 / Dưới 18.

- File cơ bản + hộ khẩu cắt từng người (nếu có).
- Gia đình: thêm `cv_1`, `cv_2`… cho người đi cùng.
- Dưới 18: thêm bộ `duoi18_`.
- Miền Nam (TAI) chỉ có L30.

### M — thương mại (công ty TQ mời người VN)

Lựa chọn: **Trong đoàn là** Người đầu / Người sau · **Người được mời là** Nhân viên / Chủ doanh nghiệp.

4 file công ty, **đúng tên**:

| Tên      | Giấy                                  | Của ai                                                                   |
| -------- | ------------------------------------- | ------------------------------------------------------------------------ |
| `thumoi` | thư mời của công ty Trung Quốc        | bên TQ (chỉ tải lên, không đọc)                                          |
| `dktq`   | đăng ký kinh doanh công ty Trung Quốc | bên TQ (chỉ tải lên)                                                     |
| `dkvn`   | đăng ký kinh doanh công ty Việt Nam   | bên VN — hệ thống đọc công ty VN + người đại diện                        |
| `qdct`   | quyết định cử đi công tác             | bên VN — hệ thống đọc công ty TQ (tên, địa chỉ, điện thoại) + ngày đi/về |

Giấy nhiều trang: `dktq_1`, `dktq_2`…

**Người được mời là chủ doanh nghiệp (giám đốc)** — không có quyết định công tác:

1. Trước khi tải lên: **chép `thumoi` thành thêm `qdct`** (cùng nội dung; nhiều trang thì chép cả `qdct_1`, `qdct_2`…) — hệ thống đọc công ty TQ và ngày đi/về từ `qdct`.
2. Sau khi chạy xong: trên trang visa, ô **"Quyết định công tác"** → xoá file đang có (thư mời) và tải lên **`dkvn`** để chứng minh là chủ doanh nghiệp.

- Tên người đi phải trùng **người đại diện** trên `dkvn`.

**Thứ tự làm file (M)**: 1) file cơ bản giữ tên gốc → 2) xác định 4 file đặc thù và đặt đúng tên
(chủ DN: chép thumoi → qdct) → 3) người đi cùng `cv_`, hộ khẩu `tt_`.

**Đi theo đoàn — người sau** (M và F): người sau chỉ cần file cơ bản (+ `cv_`, hộ khẩu nếu có),
**không cần** giấy công ty/trường. Cách làm:

1. Chạy người đầu trước, đủ file, tới khi chạy curl thành công.
2. Người sau: tải thư mục chỉ có file cơ bản → Gửi → chờ có curl.
3. Tab **Chạy curl**: Đọc curl của người sau → ở **Lịch sử curl** tìm hồ sơ người đầu (gõ số hộ chiếu) → bấm **"Áp dụng M"** (F: "Áp dụng F") → xem lại → **Chạy**.

- "Áp dụng M" chép thông tin công ty TQ/VN + ngày đi/về của người đầu và ghi số hộ chiếu người đầu vào `company_passport`. "Áp dụng F" chép trường mời, ngày học, học vấn và ghi `school_passport`.
- Khi chọn "Người sau", mục "Thứ tự làm file" ẩn, mục "Đi theo đoàn" lên thứ 2.

### F — trao đổi / học ngắn hạn

| Tên         | Giấy                                   | Của ai                 | Hệ thống                             |
| ----------- | -------------------------------------- | ---------------------- | ------------------------------------ |
| `fthumoi_1` | thư mời / giấy tiếp nhận của trường TQ | trường TQ (bên mời)    | đọc tên trường, địa chỉ, ngày đến/đi |
| `fqddh_1`   | quyết định cử đi học                   | trường VN của người đi | đọc tên trường VN, bậc học, ngành    |

Không lẫn 2 loại. Có `cv_`. Có lựa chọn Người đầu/Người sau ("Áp dụng F").
Lỗi hay gặp: đặt `thumoi` (của M/Q) thay vì `fthumoi`.

### X1 (du học > 180 ngày) / X2 (≤ 180 ngày)

| Tên     | Giấy                                         | Hệ thống                                              |
| ------- | -------------------------------------------- | ----------------------------------------------------- |
| `xnh_1` | giấy báo nhập học (录取通知书) của trường TQ | đọc tên trường, địa chỉ, ngày nhập học/kết thúc       |
| `xjw_1` | mẫu JW201 / JW202                            | đọc tên trường, ngày học (bổ sung khi giấy báo thiếu) |

Ưu tiên `xnh`, thiếu mới lấy `xjw`. Thời gian học không khớp loại (X2 mà học 1 năm) → hệ thống cảnh báo, đổi loại. Có `cv_`.

### Q1 (đoàn tụ > 180 ngày) / Q2 (thăm thân ≤ 180 ngày) — người mời là công dân TQ

Lựa chọn: **Tuổi** Từ 18 / Dưới 18 · **Chữ ký người mời** Vẽ lại nét / Chữ ký gốc (`_goc`).
**Bắt buộc chọn "Quan hệ"** ở form (người mời là gì của người xin visa); quan hệ được in vào thư mời.

| Tên                         | Giấy                                                                                  | Cần      | Hệ thống                                         |
| --------------------------- | ------------------------------------------------------------------------------------- | -------- | ------------------------------------------------ |
| `qmoi_1`                    | giấy tờ người mời (CCCD / hộ khẩu / hộ chiếu TQ, visa + dấu nhập cảnh VN) — mặt trước | bắt buộc | đọc họ tên, số giấy tờ, địa chỉ, tỉnh/thành/quận |
| `qmoi_2`                    | mặt sau / trang 2                                                                     | nếu có   | như trên                                         |
| `qmoi_3`…`qmoi_5`           | trang 3–5 — **chỉ miền Nam**; miền Bắc đặt `qkhac_`                                   | nếu có   | như trên                                         |
| `qcm_1`…`qcm_5`             | giấy chứng minh quan hệ chính (xem dưới)                                              | bắt buộc | chỉ tải lên                                      |
| `qthumoi_1`                 | thư mời **khách tự cung cấp** (đã viết, ký sẵn)                                       | nếu có   | thay thư hệ thống tạo                            |
| `qchuki_1`                  | chữ ký người mời (cho thư mời)                                                        | nên có   | làm nền trắng, đưa vào thư mời                   |
| `qbaolanh_1` (hoặc `qbl_1`) | chữ ký người bảo lãnh — ký thay người mời (vd người mời < 18 tuổi)                    | nếu có   | dùng mẫu thư mời có dòng bảo lãnh                |
| `qkhac_1`                   | giấy tờ khác + giấy quan hệ phụ                                                       | nếu có   | chỉ tải lên                                      |

**Thứ tự làm file (Q1, Q2)** — người dùng chốt, làm đúng thứ tự này để dễ làm file:

1. **`qmoi_`** — giấy tờ người Trung Quốc đang mời (CCCD, visa nhập cảnh VN, dấu nhập cảnh VN…).
   - **Miền Nam (TAI)**: `qmoi_1` → `qmoi_n`.
   - **Miền Bắc (HAI, PHONG)**: chỉ `qmoi_1`, `qmoi_2`; giấy người mời còn lại → `qkhac_`.
2. **`qcm_`** — **chỉ giấy quan hệ chính giữa 2 người** (người mời ↔ người được mời).
   Giấy quan hệ của 1 trong 2 người **với người khác** → `qkhac_`.
   Miền Bắc chỉ tải lên **Q1: 4 / Q2: 3** file `qcm_` đầu tiên → giấy quan trọng nhất để số nhỏ.
3. **Chữ ký**: gốc → `qchuki_1_goc`, không → `qchuki_1`. Cần bảo lãnh → `qbaolanh_1` (gốc: `qbaolanh_1_goc`).
4. **`qkhac_`** — mọi giấy còn lại. (Thư mời khách đưa sẵn vẫn là `qthumoi_1`, không phải `qkhac_`.)

**`qcm_` theo quan hệ người mời** (người dùng chốt):

| Quan hệ                     | `qcm_` là                                                                      | `qkhac_` là                       |
| --------------------------- | ------------------------------------------------------------------------------ | --------------------------------- |
| Vợ mời chồng / chồng mời vợ | **giấy đăng ký kết hôn** bản TQ + bản VN; bản có đóng dấu thì đưa kèm vào luôn | giấy tờ khác                      |
| Con mời mẹ / con mời bố     | **giấy khai sinh** (của người con)                                             | **ĐKKH của bố mẹ** + giấy tờ khác |
| Quan hệ khác                | giấy chứng minh đúng quan hệ đó                                                | các giấy quan hệ còn lại          |

Cùng 1 tờ ĐKKH có thể là `qcm_` ở hồ sơ này nhưng `qkhac_` ở hồ sơ khác — xem quan hệ người mời trước.
(Chưa xác nhận: bố mẹ mời con có dùng giấy khai sinh không — đã hỏi người dùng, chưa có trả lời.)

**Chữ ký `_goc`** (WF-04: `qchuki_` / `qbaolanh_` / `qbl_` / `schuki_` kết thúc `_goc`):

- `_goc`: giữ nguyên nét, chỉ làm nền trắng + chỉnh cỡ. Dùng khi ảnh chữ ký rõ, đẹp.
- Không `_goc`: làm nền trắng và **vẽ lại nét**. Dùng khi ảnh mờ, nhoè, nghiêng.
- `_goc` đặt **cuối tên**: `qchuki_1_goc`, không phải `qchuki_goc_1`.

**Thư mời**: bình thường không cần chuẩn bị — hệ thống tạo từ `qmoi` + quan hệ + chữ ký.
Có `qthumoi_1` (`qthumoi_2`… nếu nhiều trang): Q1, Q2, cả 2 miền, hệ thống tải lên đúng thư này
(gộp các trang thành 1 PDF); thư hệ thống tạo vẫn làm và lưu dự phòng `…_backup.pdf`.

**Nhiều trang theo miền**: Miền Nam gộp tất cả file cùng loại thành 1 PDF theo số thứ tự.

### S2 — thăm người thân là người nước ngoài đang ở TQ

Giống Q nhưng tiền tố `s`: `smoi_`, `scm_`, `schuki_`, `skhac_`, `sthumoi_`. **Không có bảo lãnh.**
Bắt buộc chọn "Quan hệ" (S2: "Chồng / Vợ sắp cưới" ở đầu danh sách).

| Tên               | Giấy                                                                                                                                                                                                                         |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `smoi_1`          | hộ chiếu người mời (bắt buộc)                                                                                                                                                                                                |
| `smoi_2`          | giấy cư trú / giấy phép ở TQ của người mời (bắt buộc)                                                                                                                                                                        |
| `smoi_3`…`smoi_5` | trang thêm — chỉ miền Nam; miền Bắc → `skhac_`                                                                                                                                                                               |
| `scm_1`…`scm_5`   | giấy quan hệ chính (quy tắc như `qcm_`)                                                                                                                                                                                      |
| `sthumoi_1`       | thư mời khách tự cung cấp (có thì tải lên đúng thư đó, cả 2 miền)                                                                                                                                                            |
| `smoi_ruot_1`     | giấy của **chính người mời** khi giấy `smoi` là của người khác (vd chị lấy chồng TQ mời em: `smoi` = giấy của chồng, `smoi_ruot` = giấy của chị). Địa chỉ lấy từ `smoi`; giới tính + ngày sinh người mời lấy từ `smoi_ruot`. |
| `schuki_1`        | chữ ký (cho thư mời), `_goc` như Q                                                                                                                                                                                           |
| `skhac_1`         | giấy khác + giấy quan hệ phụ                                                                                                                                                                                                 |

Thứ tự làm file: `smoi` → `scm` → `schuki` → `skhac` (quy tắc miền Bắc như Q; miền Bắc tải 3 file `scm_` đầu).
Lỗi hay gặp: dùng tiền tố Q (`qmoi_`) cho S2; `smoiruot` / `smoi_1_ruot` (phải `smoi_ruot_1`); thư mời đặt `thumoi`/`qthumoi`.

**Sang TQ để kết hôn** (quan hệ "Chồng sắp cưới" = `CHONG SAP CUOI`, mục `s2marry` trong guide.js):

- Thư mời (cả 2 miền): tick 未婚妻（夫） và mục đích 登记结婚 thay cho 探亲.
- Form COVA SaveApplyInfo, **chỉ miền Nam**: tự đổi `type_of_visa_sub_value` → `SPM` (visaType 710021, mục B 因其他私人事务), `applyReason.personalMatters` = `登记结婚`, `relation` = 未婚夫 (`flows/flow_payloads.south_s2_marriage`). Các trường khác như cũ.
- Miền Bắc: form COVA giữ theo curl, không tự đổi.

---

## 4. Code

| Thành phần                               | Vị trí                                                                                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nội dung hướng dẫn + hàm vẽ (dùng chung) | `web/guide.js`                                                                                                                                                      |
| CSS hướng dẫn (dùng chung)               | `web/guide.css`                                                                                                                                                     |
| Popup trong form                         | `web/index.html` (markup `#guide`, `#exDlg`; JS `renderGuide`, `openGuide`, `loadExamples`)                                                                         |
| Trang riêng                              | `web/guide.html` (server thay `__HOUSES__` bằng JSON danh sách nhà)                                                                                                 |
| Route                                    | `server.py`: `GET /web/huong-dan`, `GET /web/guide.js`, `GET /web/guide.css` (no-cache), `GET /web/guide/{path}` (ảnh), `GET/POST/DELETE /web/guide-examples/{key}` |
| Ảnh ví dụ ADMIN tải lên                  | `web/guide/vd/<key>/` (không có trong git)                                                                                                                          |
| Ảnh mẫu có sẵn (khi ADMIN chưa thêm)     | `web/guide/vd_default/<key>/` (trong git)                                                                                                                           |
| Ảnh thật thay hình vẽ minh hoạ           | `web/guide/L/<tên>.jpg` (xem `web/guide/README.md`)                                                                                                                 |

`/web` và mọi đường dẫn con là public trong access guard (`ACCESS_PUBLIC_PATHS` mặc định `/health,/web`);
POST/DELETE ảnh ví dụ tự kiểm tra ADMIN (`_web_admin`).

### Cấu trúc `web/guide.js`

- `GUIDES[code] = { title, intro, options, sections }`.
  - `options`: `true` (dùng `guideOptions()` mặc định của L) hoặc hàm trả HTML các nút lựa chọn.
  - `sections[]`: `{ id, title, hint, open, when(opt, house), html(opt, house) }`. Số thứ tự mục tự đánh khi render (ẩn mục nào cũng không nhảy số).
- `guideOpt = { kind, order, u18, owner, goc }` — trạng thái lựa chọn. `GUIDE_BOOL` = các khoá kiểu bool.
  `GUIDE_OPEN_ON` = mục nào tự mở khi đổi lựa chọn.
- `seg(key, items)` vẽ nhóm nút lựa chọn (class `.seg`, nút có `data-k`, `data-v`).
- `typeGuide({...})` tạo hướng dẫn cho F, X1, X2, Q1, Q2, S2 (tham số `docs`, `docsNote`, `extra`, `errors`, `group`, `companions`, `u18`, `sign`, `steps`).
  `steps` = section object (`inviteSteps(...)`) hoặc chuỗi HTML các file đặc thù (→ `specialSteps`).
- M được viết riêng (`GUIDES.M`), dùng lại `specialSteps`, `groupSection`, `companionSection`, và các mục `basic`, `hokhau` của L.
- Hàm dùng chung cho cả 2 trang: `guideFill(body, visa, house)`, `guidePick(btn, body, fill)`, `guideToggleAll(body)`, `guideExamples(key)`, `guideExGrid(key, ex, canDelete)`, `guidePageUrl(visa, house)`.
- Ảnh ví dụ: key = tên file bỏ số cuối (`exKey`), trừ `qmoi_1..3`, `smoi_1..3` (mỗi số là giấy khác); `con_N` → `con_cai` (Windows cấm thư mục tên `con`).
  Sơ đồ thư mục dùng tên mẫu `IMG_2041` (hộ chiếu), `IMG_2042` (ảnh thẻ), `scan_01/02` (trang trắng), `ct07`, `visa2023` → map qua `TREE_EX`.

### Bẫy đã gặp (đừng lặp lại)

- `guide.js` là classic script nạp **trước** script trang và **chạy code ngay lúc tải** → nó tự định nghĩa `esc()`. Đừng xoá `esc` khỏi `guide.js`; trang không được khai báo lại `const`/`let` trùng tên với `guide.js`.
- `const` dùng trước khi khai báo → `ReferenceError` làm **trắng cả popup lẫn trang riêng**. Hàm builder (vd `specialSteps`) phải đặt **trên** chỗ `GUIDES.M` / `typeGuide` dùng nó.
- Sửa nội dung thì sửa ở `web/guide.js` — popup và trang riêng tự đổi theo.

### Kiểm tra sau khi sửa

1. `node --check web/guide.js`
2. Chạy server cục bộ không cần DB (stub weasyprint, `lifespan="off"`), ví dụ script:
   ```python
   import sys, types, uvicorn
   m = types.ModuleType("weasyprint"); m.HTML = m.CSS = object; sys.modules["weasyprint"] = m
   import server
   uvicorn.run(server.app, host="127.0.0.1", port=18765, lifespan="off")
   ```
3. Chrome headless:
   - liệt kê mục: `chrome --headless=new --enable-logging=stderr --v=0 --virtual-time-budget=3000 --dump-dom "http://127.0.0.1:18765/web/huong-dan?visa=Q2&house=HAI"` → grep `<summary>`; grep `CONSOLE` trong stderr để bắt lỗi JS.
   - chụp: `--screenshot=... --window-size=1280,1500`.
   - Thử đủ: mỗi `visa`, nhà Bắc (HAI) và Nam (TAI), `order=sau`, `owner=true`, `u18=true`, `kind=giadinh`.
4. `python -m unittest tests.test_web_portal`

Tham số URL trang riêng: `visa`, `house`, `kind` (canhan|giadinh), `order` (dau|sau), `u18`, `owner`, `goc` (true|false).

---

## 5. Quy ước làm việc với người dùng

- Trả lời người dùng bằng **tiếng Việt**.
- Repo một người: commit và push thẳng lên `main`, không tạo nhánh. Người dùng hay gõ "push" sau mỗi thay đổi.
- Thay đổi nghiệp vụ hướng dẫn: hỏi lại khi quy tắc chưa rõ, ghi rõ chỗ mình tự suy ra.
- Không chạy truy vấn vào DB production khi chưa được đồng ý .
