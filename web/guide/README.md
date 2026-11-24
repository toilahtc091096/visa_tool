# Ảnh ví dụ cho popup "Hướng dẫn file" (trang /web)

Popup vẽ sẵn hình minh hoạ. Đặt ảnh thật vào đây thì popup tự dùng ảnh thật
(phục vụ qua `GET /web/guide/<loại>/<tên>`, chỉ nhận .jpg/.jpeg/.png/.webp).

**Ai có link đều xem được ảnh ở đây: chỉ dùng ảnh mẫu hoặc đã che thông tin.**

Loại L (`web/guide/L/`):

| File | Hiện ở |
|---|---|
| `ho_chieu.jpg`, `anh_the.jpg`, `ct07.jpg`, `visa_cu_1.jpg` | mục 2 – File cơ bản |
| `ho_khau_goc.jpg` | mục 3 – ảnh cũ (trang hộ khẩu nhiều người) |
| `tt_cha.jpg`, `tt_me.jpg`, `vo_chong.jpg`, `con_1.jpg`, `con_2.jpg` | mục 3 – ảnh mới sau khi cắt |

Nội dung chữ của hướng dẫn nằm trong `web/index.html`, hằng `GUIDES` (thêm loại khác: thêm khoá `M`, `Q1`…).
