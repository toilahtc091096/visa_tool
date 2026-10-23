# zalo-bridge

Cầu nối giữa Zalo (thư viện [zca-js](https://github.com/RFS-ADRENO/zca-js)) và Python server (`services/application_status_tracker.py`).

## Chạy

```bash
cd zalo-bridge
npm install
cp .env.example .env   # sửa ZALO_BRIDGE_SECRET, PYTHON_BASE_URL
npm start
```

- Lần đầu: mở `qr.png` và quét bằng app Zalo của tài khoản bot. Cookie được lưu vào `credentials.json`, các lần sau tự đăng nhập lại.
- Lấy id nhóm: `curl -H "x-bridge-secret: <secret>" http://127.0.0.1:3100/groups`, rồi điền vào `TRACKER_ZALO_GROUP_ID` (cả `.env` của bridge và của Python).
- Lấy id người gửi: xem log `inbound group=... sender=...` khi người đó nhắn vào nhóm.
- Một tài khoản Zalo chỉ giữ được 1 listener. Mở Zalo Web cùng tài khoản sẽ làm bridge bị ngắt (`closed code=3000`).

## Endpoint

| Method | Path | Mô tả |
|---|---|---|
| POST | `/send` | `{thread_id, thread_type: "group" \| "user", text}` |
| GET | `/groups` | Danh sách id + tên nhóm |
| GET | `/health` | Kiểm tra sống |

Mọi request cần header `x-bridge-secret` nếu đã đặt `ZALO_BRIDGE_SECRET`.
