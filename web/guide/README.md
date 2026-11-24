# Ảnh ví dụ cho popup "Hướng dẫn file" (trang /web)

Popup vẽ sẵn hình minh hoạ. Đặt ảnh thật vào đây thì popup tự dùng ảnh thật
(phục vụ qua `GET /web/guide/<loại>/<tên>`, chỉ nhận .jpg/.jpeg/.png/.webp).

**Ai có link đều xem được ảnh ở đây: chỉ dùng ảnh mẫu hoặc đã che thông tin.**

Loại L (`web/guide/L/`):

| File | Hiện ở |
|---|---|
| `hochieu.jpg`, `anhthe.jpg`, `trangtrang_1.jpg`, `ct07_1.jpg`, `visacu_1.jpg` | mục File cơ bản |
| `ho_khau_goc.jpg` | mục Hộ khẩu – ảnh cũ (trang hộ khẩu nhiều người) |
| `tt_cha.jpg`, `tt_me.jpg`, `vo_chong.jpg`, `con_1.jpg`, `con_2.jpg` | mục Hộ khẩu – ảnh mới sau khi cắt |

Nội dung chữ của hướng dẫn nằm trong `web/index.html`, hằng `GUIDES` (thêm loại khác: thêm khoá `M`, `Q1`…).

## Ảnh ví dụ theo loại file (nút "🖼 Ảnh ví dụ")

Mỗi file trong bảng hướng dẫn (M, F, X1, X2, Q1, Q2, S2, người thân, dưới 18, cv_) có nút **Ảnh ví dụ**.
Bấm vào mở popup hiện các ảnh mẫu của loại file đó.

**Thêm / xoá ảnh (tài khoản ADMIN):** đăng nhập /web bằng ADMIN → mở "Hướng dẫn file" → bấm "🖼 Ảnh ví dụ"
của file cần làm → **＋ Thêm ảnh** (chọn 1 hoặc nhiều ảnh .jpg/.png/.webp, ≤ 8 MB từ máy) hoặc **Xoá** dưới từng ảnh.
Nhân viên khác chỉ xem.

- Ảnh lưu trên VPS ở `web/guide/vd/<loại>/` (không nằm trong git, `git pull` không đụng tới). Sao lưu thư mục này nếu cài lại VPS.
- `<loại>` = tên file bỏ số cuối: `cv_1`, `cv_2` → `cv`; `qcm_1` → `qcm`; `qchuki_1` (cả `_goc`) → `qchuki`;
  `con_1`, `con_2` → `con_cai` (Windows không cho thư mục tên `con`).
  Riêng `qmoi_1`, `qmoi_2`, `qmoi_3`, `smoi_1`, `smoi_2`, `smoi_3` mỗi số 1 loại (mặt trước / mặt sau / trang 3–5).
