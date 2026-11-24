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
Bấm vào mở popup hiện **mọi ảnh** trong thư mục `web/guide/vd/<loại>/` (xếp theo tên, nhận .jpg/.jpeg/.png/.webp).

- Thêm / đổi ảnh: thả hoặc đè ảnh vào đúng thư mục, không cần sửa code. Xoá ảnh thì popup bớt ảnh đó.
- Hiện có ảnh tạm `1.jpg`, `2.jpg` ghi đường dẫn của chính nó: đè ảnh thật lên (hoặc xoá đi).
- `<loại>` = tên file bỏ số cuối: `cv_1`, `cv_2` → `vd/cv/`; `con_1`, `con_2` → `vd/con_cai/` (Windows không cho thư mục tên `con`); `qcm_1` → `vd/qcm/`;
  `qchuki_1` (cả `_goc`) → `vd/qchuki/`. Riêng `qmoi_1`, `qmoi_2`, `qmoi_3`, `smoi_1`, `smoi_2`, `smoi_3` mỗi số 1 thư mục (mặt trước / mặt sau / trang 3–5).

Thư mục có sẵn: `cv`, `con_cai`, `tt_cha`, `tt_me`, `vo_chong`, `duoi18_ks`, `duoi18_dc1`, `duoi18_dc2`, `duoi18_pay`,
`thumoi`, `dktq`, `dkvn`, `qdct`, `fthumoi`, `fqddh`, `xnh`, `xjw`, `qmoi_1`, `qmoi_2`, `qmoi_3`, `qthumoi`, `qcm`, `qchuki`, `qbaolanh`, `qkhac`,
`smoi_1`, `smoi_2`, `smoi_3`, `scm`, `sthumoi`, `smoi_ruot`, `schuki`, `skhac`.
