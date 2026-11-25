# VISA BRANDING KIT

Bộ nhận diện tối giản cho website **Khai hồ sơ visa / Thống kê hồ sơ**.

## 1. Thành phần
- `favicon.ico` — favicon đa kích thước 16, 32, 48 px
- `favicon.svg` — biểu tượng vector
- `apple-touch-icon.png` — 180 × 180
- `icon-192.png` — 192 × 192
- `icon-512.png` — 512 × 512
- `icon-maskable-512.png` — 512 × 512, vùng an toàn cho Android/PWA
- `og-image.png` — 1200 × 630, ảnh chia sẻ mạng xã hội
- `tampermonkey-icon.png` — 64 × 64
- `logo.svg` — logo ngang vector
- `site.webmanifest` — cấu hình PWA

## 2. Bảng màu
- Navy: `#102A43`
- Ocean Blue: `#087EAA`
- Ice Blue: `#DCEAF2`
- Silver White: `#F5F8FA`

## 3. Đưa file vào website
Sao chép toàn bộ file trong thư mục này vào thư mục tĩnh được server phục vụ tại URL gốc `/`.
Ví dụ: nếu `web/` đang là thư mục tĩnh public thì đặt các file vào `web/`. Nếu server dùng thư mục khác, hãy đặt tại thư mục tương ứng và chỉnh đường dẫn URL trong HTML/manifest.

## 4. HTML cho cả `web/index.html` và `web/stats.html`
Trong `<head>`, xóa dòng cũ:
```html
<link rel="icon" href="data:,">
```
Sau đó thêm:
```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#102A43">
<meta property="og:image" content="/og-image.png">
```

## 5. Logo ở header
Trong header của cả hai trang, thay phần tiêu đề chữ hiện tại bằng:
```html
<a class="brand" href="/" aria-label="Khai hồ sơ visa">
  <img src="/logo.svg" alt="Khai hồ sơ visa" class="brand-logo">
</a>
```
CSS gợi ý:
```css
.brand { display:inline-flex; align-items:center; text-decoration:none; }
.brand-logo { display:block; width:min(300px, 58vw); height:auto; }
```
Nếu header nền tối, dùng logo ngang vẫn có chữ navy; nên đặt logo trên nền sáng hoặc dùng biến thể chữ trắng. Biểu tượng độc lập có nền navy, phù hợp thanh điều hướng tối.

## 6. Phục vụ file từ `server.py`
Nếu đang dùng `http.server.SimpleHTTPRequestHandler`, khởi chạy server với thư mục gốc `web/` là đủ để phục vụ các file đặt trong `web/`.

Nếu dùng handler tự viết, thêm route tương ứng (điều chỉnh `WEB_DIR` theo cấu trúc thực tế):
```python
from pathlib import Path
from flask import send_from_directory  # nếu dự án đang dùng Flask

WEB_DIR = Path(__file__).parent / "web"

@app.get("/favicon.ico")
def favicon():
    return send_from_directory(WEB_DIR, "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.get("/favicon.svg")
def favicon_svg():
    return send_from_directory(WEB_DIR, "favicon.svg", mimetype="image/svg+xml")

@app.get("/site.webmanifest")
def webmanifest():
    return send_from_directory(WEB_DIR, "site.webmanifest", mimetype="application/manifest+json")

@app.get("/<path:asset>")
def branding_asset(asset):
    allowed = {
        "apple-touch-icon.png", "icon-192.png", "icon-512.png",
        "icon-maskable-512.png", "og-image.png", "logo.svg",
        "tampermonkey-icon.png"
    }
    if asset not in allowed:
        abort(404)
    return send_from_directory(WEB_DIR, asset)
```
Lưu ý: chỉ thêm route Flask nếu server thực sự dùng Flask. Không tạo route catch-all làm ảnh hưởng các route API hiện có; đặt các route cụ thể trước route fallback.

## 7. Tampermonkey
Trong metadata block đầu script, thêm hoặc cập nhật:
```javascript
// @icon        https://YOUR_DOMAIN/icon-192.png
```
Thay `https://YOUR_DOMAIN` bằng domain thực tế. Tampermonkey cần URL truy cập được; nếu script chạy nội bộ, dùng URL tuyệt đối tới server nội bộ phù hợp.

## 8. Kiểm tra sau tích hợp
- Mở `/favicon.ico`, `/favicon.svg`, `/site.webmanifest`, `/logo.svg`.
- Kiểm tra DevTools → Network không còn 404.
- Kiểm tra hai trang đều hiển thị logo và màu thanh trình duyệt navy.
- Nếu trình duyệt giữ favicon cũ, hard refresh hoặc đổi query version, ví dụ `/favicon.svg?v=2`.

## 9. Ghi chú
Logo và icon trong bộ này dùng cùng một biểu tượng hộ chiếu + địa cầu + chữ V, ưu tiên tương phản tốt ở kích thước nhỏ. `icon-maskable-512.png` đặt biểu tượng trong vùng an toàn trung tâm để tránh bị cắt khi hệ điều hành áp dụng mặt nạ hình tròn/bo góc.
