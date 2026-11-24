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
