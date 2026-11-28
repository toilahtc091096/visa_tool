# update.md — Kế hoạch cải tiến (làm từng bước, theo dõi kết quả)

Ba mảng: **U** = đo tỉ lệ duyệt, **K** = kiểm tra hồ sơ khi tải lên, **HK** = mở rộng sang visa Hồng Kông.

Mỗi hạng mục ghi 3 phần (giống `docs/n8n-improvement-tracker.md`):

- **Ban đầu**: đang chạy thế nào, ghi **trước khi sửa**, sau đó không sửa lại.
- **Kỳ vọng**: tiêu chí đo được, mỗi tiêu chí trả lời được "đạt / không đạt". Viết trước khi làm.
- **Hiện tại**: kết quả thật sau khi chạy trên hồ sơ thật (ghi ngày + kết quả từng tiêu chí).

Trạng thái: `Chưa làm` · `Đang làm` · `Chờ test` · `Đạt` · `Không đạt` · `Bỏ` · `Tạm hoãn`

Quy tắc: mỗi lần làm 1–2 hạng mục, xong (Đạt) mới sang hạng mục sau. Quy tắc nghiệp vụ chưa rõ → hỏi lại, ghi rõ chỗ tự suy ra.

---

## 0. Bảng tổng

| Mã  | Việc                                                                    | Phụ thuộc | Trạng thái | Cập nhật   |
| --- | ----------------------------------------------------------------------- | --------- | ---------- | ---------- |
| U1  | Đo tỉ lệ duyệt hiện tại (truy vấn chỉ đọc trên VPS)                     | —         | Đạt        | 2026-11-28 |
| U2  | Ghi lịch sử đổi trạng thái (để đo "duyệt ngay lần đầu", thời gian duyệt) | U1        | Chưa làm   |            |
| K1  | Gom quy tắc tên file về 1 file (`web/file_check.js`)                     | —         | Chờ test   | 2026-11-28 |
| K2  | Kiểm tra cấp 1 trong form `/web` (tên file, thiếu giấy, giới hạn miền)   | K1        | Chờ test   | 2026-11-28 |
| K3  | Trang trắng miền Bắc: 1 file thì điền cả 2 ô `mfa-017`                   | —         | Bỏ         | 2026-11-28 |
| K7  | M: so khớp tên công ty TQ giữa thư mời / quyết định / ĐKKD               | —         | Chưa làm   |            |
| K4  | n8n WF-04 nhận diện theo cùng file quy tắc                               | K1        | Chưa làm   |            |
| K5  | Kiểm tra cấp 2: AI xem nội dung file cơ bản trước khi Gửi                | K2        | Chưa làm   |            |
| K6  | Kiểm tra cấp 3: quy tắc mới từ lý do bị trả                              | U1, K2    | Chưa làm   |            |
| HK1 | Khảo sát visa Hồng Kông (nhu cầu đại lý + quy trình + kênh nộp)          | —         | Tạm hoãn   |            |
| HK2 | Khai thử tay 1–3 bộ HK, ghi lại form / API                              | HK1       | Tạm hoãn   |            |
| HK3 | Tách "hồ sơ khách" chuẩn hoá khỏi body COVA                              | HK2       | Tạm hoãn   |            |
| HK4 | MVP Hồng Kông                                                           | HK3       | Tạm hoãn   |            |

---

## U. Tỉ lệ duyệt

### U1 — Đo tỉ lệ duyệt hiện tại

**Ban đầu**
- Trạng thái lấy từ COVA qua đồng bộ (`services/visa_registration_sync.py`):
  `待提交`→draft, `已提交`→submitted, `待审核`→pending_review, `初审中`→under_review,
  `驳回待修改`→needs_fix, `审核通过`→approved, `审核未通过`→rejected, `已撤销/已取消`→cancelled.
- Lý do trả: `payload->'sync'->'matched_row'->>'rejectReason'`.
- **Lưu ý ý nghĩa:** đây là kết quả **duyệt đơn online trên COVA**, chưa phải kết quả cấp visa cuối cùng.
- DB chỉ giữ **trạng thái hiện tại** → hồ sơ từng bị `needs_fix` rồi được duyệt thì giờ chỉ thấy `approved`
  (không đo được "duyệt ngay lần đầu" → U2).

**Kỳ vọng**
1. Có bảng: theo nhà, theo loại visa, theo tháng, theo đại lý: tổng / nháp / đang xử lý / đợi sửa / duyệt / từ chối / huỷ / % duyệt.
2. Có top lý do trả (rejected + needs_fix).
3. Biết dữ liệu có "tươi" không (nháp cũ > 14 ngày, lần cập nhật cuối mỗi nhà).
4. Chốt 1 con số dùng để chào đại lý (ghi vào "Hiện tại").

**Hiện tại** (2026-11-28, chạy trên VPS, DB `visa_main`) — **Đạt**

Tổng: 3.161 hồ sơ (16/06 → 28/11/2026). Đã có kết quả (duyệt + từ chối): 2.964, **duyệt 2.928 = 98,8 %**.
Số lượng tăng đều: 504 (T7) → 571 → 598 → 641 → 695 (T11).

| Nhóm visa         | Đã có kết quả | Duyệt | Từ chối | % duyệt | % số hồ sơ |
| ----------------- | ------------- | ----- | ------- | ------- | ---------- |
| L (L15 + L30)     | 2.518         | 2.509 | 9       | 99,6    | 84 %       |
| M (mọi số ngày)   | 248           | 242   | 6       | 97,6    | 8 %        |
| **Q (Q1 + Q2)**   | 151           | 130   | **21**  | **86,1** | 6 %       |
| F, S2, X          | 47            | 47    | 0       | 100     | 2 %        |

Theo nhà: HAI 99,4 % · PHONG 97,8 % · TAI 100 % (mới chạy từ 08/11, 102 hồ sơ).

Phát hiện:
1. **Q chiếm 58 % số bị từ chối (21/36) dù chỉ 6 % số hồ sơ.** Q1 81 %, Q2 (180 ngày) 88 %.
   Lý do đọc được gần như đều là **vợ/chồng TQ**: thiếu tường trình quá trình quen biết → kết hôn
   (có khi đòi tiếng Trung), ảnh chụp chung (2025–2026), lịch sử trò chuyện, hộ chiếu chồng trong ĐKKH,
   CT07 phù hợp, thư mời ký lại / sai quan hệ trên thư mời, nghi giấy tờ không thật (材料造假).
   → Không phải lỗi đánh máy mà là **thiếu bằng chứng quan hệ**. Người dùng chốt **không kiểm** (để `qkhac_`, trung tâm cho bổ sung sau).
2. M: 1 hồ sơ huỷ vì **tên công ty TQ trên quyết định + mục 6.2A + ĐKKD không khớp thư mời** → tool so được (K7).
   M60: 2/3 bị từ chối (ít mẫu, theo dõi tiếp).
3. **Thiếu lý do**: 26/36 từ chối và 28/32 huỷ có lý do trống → khó học từ lỗi. Cần lưu lý do + lịch sử (U2).
4. T10–T11 số từ chối tăng (12, 11) so với 2–4 các tháng trước; T11 còn nhiều hồ sơ đang xử lý. Chưa rõ do
   loại visa nào → truy vấn bổ sung (từ chối theo tháng × loại visa).
5. Miền Bắc hầu hết hồ sơ **không gắn đại lý** (HAI 1.623, PHONG 1.018 "(không)"; chỉ gần đây có `MB`)
   → chưa đo được theo từng đại lý ở miền Bắc. Muốn chào đại lý bằng số liệu riêng của họ thì phải gắn mã đại lý cho cả miền Bắc.
6. 3.161 hồ sơ / 2.970 số hộ chiếu → ~190 bản ghi trùng hộ chiếu (chạy lại hoặc khách quay lại; chưa tách được).
   HAI có 28 nháp > 14 ngày (bỏ dở hoặc bản chạy lại).

**Con số dùng chào đại lý** (nói đúng: duyệt đơn online COVA, không phải kết quả cấp visa):
> 6 tháng, gần 3.000 hồ sơ có kết quả, **98,8 % được duyệt online**; du lịch (L) **99,6 %**.
> Khai bộ phức tạp nhất ~15 phút, bộ đơn giản ~4 phút, không lỗi đánh máy.

### U2 — Lịch sử trạng thái

**Kỳ vọng**
1. Bảng mới `visa_status_history (record_id, old_status, new_status, reject_reason, changed_at)`, ghi khi đồng bộ thấy trạng thái đổi.
2. Tính được: % duyệt ngay lần đầu (không qua `needs_fix`), thời gian từ nộp đến duyệt (trung vị, theo loại visa).
3. Trang thống kê ADMIN hiện 2 số trên.

---

## K. Kiểm tra hồ sơ khi tải lên

### Ban đầu (chung cho K)
- Form `/web` đọc cây thư mục (`web/index.html`, `walk()` / `uploadPicked()`) rồi tải thẳng từng file lên R2 (`/web/upload`), **không kiểm tra tên**.
- Sai tên / thiếu giấy chỉ lộ ra sau khi n8n chạy xong, hoặc không lộ (n8n bỏ qua file).
- Quy tắc tên file nằm 3 nơi, dễ lệch:
  - `web/guide.js` (hướng dẫn cho người đọc),
  - n8n WF-04 node "Detect Processing Group" (nhận diện thật; khá lỏng: tên có từ `me`, `cha`, `con` là vào nhóm người thân),
  - `services/web_portal.py` (`pick_old_visas`, `pick_inviter_doc`).

### K1 — File quy tắc chung `web/file_check.js`

(Đổi từ `.json` sang `.js`: quy tắc cần cả hàm, vd chép lại cách n8n xếp file theo tên.)

**Kỳ vọng**
1. Một file mô tả: tiền tố, loại visa dùng được, bắt buộc hay không, số file tối đa theo miền, mẫu tên đúng, lỗi hay gặp → tên gợi ý.
2. `guide.js` vẫn hiển thị như cũ (không đổi nội dung hướng dẫn khi chưa được duyệt).
3. Có test cho các quy tắc; có test so với code thật của n8n.

**Hiện tại** (2026-11-28) — **Chờ test**
- `web/file_check.js`: `n8nGroup()` chép lại node "Detect Processing Group" của WF-04 (cùng thứ tự kiểm); `checkFolder()` chạy 16 quy tắc K2.
- `tests/file_check_cases.js` (Node, 109 test) + `tests/test_file_check.py` (chạy trong unittest): 10 thư mục đúng không bị báo gì; mỗi quy tắc có test; **47 tên file so với code n8n thật** (khi có bản export `n8n-flow/workflows/`) → khớp hết. n8n đổi cách nhận tên thì test này báo.
- `guide.js` chưa đổi (đạt tiêu chí 2).

### K2 — Kiểm tra cấp 1 trong form

Chạy trong trình duyệt ngay khi kéo thư mục / đổi loại visa / đổi nhà / đổi lựa chọn. Hiện bảng ✅ ⚠️ ❌ từng file, nút **Đổi tên** (đổi `relative_path` trước khi tải). Có ❌ → không cho Gửi; chỉ ⚠️ → Gửi sau khi xác nhận.

Quy tắc (nháp, cần duyệt trước khi code):

| #   | Quy tắc                                                                                               | Mức |
| --- | ----------------------------------------------------------------------------------------------------- | --- |
| 1   | Tên có dấu tiếng Việt / dấu cách / ký tự ngoài `a-z A-Z 0-9 _ -`                                      | ⚠️ (gợi ý tên không dấu) |
| 2   | Đuôi không hỗ trợ (`.heic`, `.doc`…), file 0 byte, file quá lớn                                       | ❌ |
| 3   | Tiền tố không thuộc loại visa đang chọn (`qmoi_` trong S2, `thumoi` trong F, `fthumoi` trong M…)       | ❌ |
| 4   | Sai dạng tên: `cv1`, `smoi_1_ruot`, `smoiruot`, `qchuki_goc_1`                                         | ❌ (gợi ý tên đúng) |
| 5   | Trùng tên khác đuôi (`tt_cha.jpg` + `tt_cha.png`), nhảy số (`qcm_1`, `qcm_3`)                          | ⚠️ |
| 6   | **File cơ bản tối thiểu**: hộ chiếu + ảnh thẻ; **miền Bắc thêm ít nhất 1 trang trắng** (xem K3)         | ⚠️ (cấp 1 chỉ đếm số file không tiền tố; cấp 2 mới biết chắc là giấy gì) |
| 7   | Q1/Q2: thiếu `qmoi_1` hoặc không có `qcm_`; S2: thiếu `smoi_1` / `smoi_2` / `scm_`                     | ❌ |
| 8   | Q/S2: chưa chọn "Quan hệ"                                                                             | ❌ |
| 9   | M người đầu: thiếu 1 trong `thumoi`, `dktq`, `dkvn`, `qdct`                                            | ❌ |
| 10  | F: thiếu `fthumoi` hoặc `fqddh`; X1/X2: thiếu cả `xnh` lẫn `xjw`                                       | ❌ |
| 11  | Miền Bắc: `qmoi_3`+ / `smoi_3`+ → nên chuyển sang `qkhac_` / `skhac_`                                  | ⚠️ |
| 12  | Miền Bắc: `qcm_` quá 4 (Q1) / 3 (Q2), `scm_` quá 3 → liệt kê file sẽ không được tải lên               | ⚠️ |
| 13  | Chọn "Dưới 18" mà thiếu `duoi18_ks` hoặc `duoi18_dc1` / `duoi18_dc2`                                   | ❌ |
| 14  | L gia đình / M / F / X: có người đi cùng mà không có `cv_N`                                            | (chỉ nhắc, không kiểm được) |
| 15  | ~~Q1/Q2 vợ/chồng: nhắc bằng chứng quan hệ~~ — **Bỏ (2026-11-28)**: để chung `qkhac_`; trung tâm nhận bổ sung sau, không cần kiểm | — |

**Kỳ vọng**
1. Mỗi quy tắc trên có test (JS chạy bằng Node, không cần trình duyệt).
2. Thử lại 10 thư mục hồ sơ cũ từng lỗi tên file: bắt được ≥ 9.
3. Thử 10 thư mục hồ sơ đúng: **0** báo ❌ sai (không chặn nhầm).
4. Kiểm tra < 1 giây với thư mục 50 file.

**Hiện tại** (2026-11-28) — **Chờ test** (tiêu chí 1 đạt; 2, 3 cần chạy trên hồ sơ thật; 4 cần đo trên máy nhân viên)
- Form `/web`: khung kiểm tra ngay dưới ô thư mục, chạy lại khi đổi thư mục / visa / nhà / quan hệ.
  **Giai đoạn đầu (người dùng chốt 2026-11-28): không chặn.** ❌ và ⚠️ đều hỏi "Vẫn gửi / Xem lại".
  Khi chạy thật hết báo nhầm → đổi `FC_BLOCK_ERRORS = true` trong `web/index.html` để ❌ chặn hẳn. Nút **Đổi tên** đổi tên file khi tải lên (file trên máy giữ nguyên).
  Chỉ kiểm khi lần Gửi đó có tải thư mục từ máy (chỉ gõ thư mục R2 thì không kiểm).
- Đã thử trên Chrome headless: hiện lỗi, Đổi tên, chặn Gửi, đổi visa, Làm mới → đúng.
- Chỗ làm khác bảng quy tắc (cần người dùng xem):
  - M / F thiếu giấy công ty / trường (thiếu hết hay thiếu một phần) → chỉ ⚠️ "người sau trong đoàn thì PHẢI bấm Áp dụng M / F"
    (người dùng chốt 2026-11-28: không thêm ô "Người sau" vào form). Quy tắc 9, 10 đổi từ ❌ thành ⚠️ cho M, F; X vẫn ❌.
  - Dưới 18: form không có ô "Dưới 18" → có ít nhất 1 file `duoi18_` thì phải đủ `ks`, `dc1`, `dc2`.
  - `qchuki_goc_1`, `smoiruot`, `qmoi1`: n8n **vẫn nhận đúng** → chỉ ⚠️ (gợi ý tên chuẩn), không chặn. `cv1`, `con1`, `smoi_1_ruot`, `duoi18ks`: n8n **không nhận** → ❌.
  - Dung lượng: ⚠️ trên 15 MB, ❌ trên 50 MB (chưa có giới hạn thật trên server, số tự đặt).
  - Đuôi được nhận: jpg, jpeg, png, webp, pdf.
  - Thêm **quy tắc 16** (⚠️): tên tự do có từ khoá n8n (vd `anh_me.jpg`, `con_dau.jpg`) → n8n hiểu là mẹ / con… → báo trước.
  - Miền Bắc Q2: code upload hiện nhận **4** file `qcm_` (`_qcm_slot_files`, commit 0103caa), hướng dẫn (`guide.js`, HUONGDAN.md) vẫn ghi **3** → bộ kiểm tra theo code (4). Người dùng chốt (2026-11-28): **giữ 4 như code**, không sửa code lẫn hướng dẫn.
- Test Python có sẵn đang lỗi (có từ trước, không do K2): `test_every_upload_folder_has_a_cova_slot` (9 loại) và `test_flow_snapshots` — chạy trên `main` sạch cũng lỗi y hệt.

### K3 — Trang trắng miền Bắc: 1 file điền cả 2 ô

**Bỏ (2026-11-28)**: người dùng xác nhận logic hiện tại đúng, không sửa.

**Ban đầu**: `flows/flow_step/step_07_upload_files.py` ghép file vào ô bằng `zip(item.codes, files)` → 1 file trang trắng chỉ vào `mfa-017_1`, ô `_2` trống.

**Kỳ vọng** (cần người dùng xác nhận cách hiểu "up 2 lần được"):
1. Miền Bắc, `PASSPORT_BLANK_PAGES` chỉ có 1 file → file đó tải lên cả `_1` và `_2`.
2. Có 2 file → như cũ.
3. Snapshot test: các loại / trường hợp khác không đổi.

### K7 — M: so khớp tên công ty TQ giữa các giấy
**Ban đầu**: 1 hồ sơ M bị huỷ vì tên công ty TQ trên quyết định, mục 6.2A và ĐKKD không khớp thư mời (U1).
**Kỳ vọng**: sau khi n8n đọc xong, nếu tên công ty TQ (từ `qdct`) khác tên trên `thumoi` / `dktq` → báo ở curl / tab Chạy curl trước khi chạy `/run`.

### K4 — n8n dùng cùng file quy tắc
**Kỳ vọng**: node "Detect Processing Group" đọc quy tắc tiền tố từ server (hoặc bản sinh ra từ `file_rules.json`); bỏ khớp lỏng `me` / `cha` / `con`; bộ hồ sơ test (tracker mục 2) cho body curl không đổi.

### K5 — Kiểm tra cấp 2 (nội dung)
**Kỳ vọng**: trước khi Gửi, server phân loại nhanh các file không tiền tố (cùng model WF-04) → báo: thiếu hộ chiếu / ảnh thẻ / trang trắng (Bắc), hộ chiếu còn < 6 tháng, ảnh mờ / loá, tên hộ chiếu ≠ tên thư mục. Ghi chi phí AI mỗi hồ sơ.

### K6 — Quy tắc từ lý do bị trả
**Kỳ vọng**: từ top lý do trả (U1) chọn những lý do kiểm được từ file → thêm vào `file_rules.json`; đo lại tỉ lệ `needs_fix` sau 1 tháng.

---

## HK. Visa Hồng Kông

> **Tạm hoãn (2026-11-28)**: làm sau, ưu tiên U + K trước.

### Đã biết (cần kiểm lại trên trang chính thức trước khi dựa vào)
- Công dân Việt Nam (hộ chiếu phổ thông) cần visa vào Hồng Kông. Visa do **Sở Di trú Hồng Kông (ImmD)** cấp, **không phải** lãnh sự quán Trung Quốc → **không dùng COVA**.
- Từ 25/10/2023, người Việt Nam đủ điều kiện được xin **visa thăm nhiều lần**, mỗi lần ở tối đa 14 ngày. Điều kiện theo báo chí: đã ra nước ngoài ≥ 3 lần, tới ≥ 2 nước trong 3 năm gần nhất, hoặc từng làm việc / học ở HK.
- ImmD có hệ thống **e-Visa**: nộp đơn, thanh toán và nhận visa điện tử online.
- Nguồn: [ImmD FAQ visit/transit](https://www.immd.gov.hk/eng/faq/visit-transit.html), [VnExpress](https://e.vnexpress.net/news/travel/hong-kong-relaxes-visa-rules-for-vietnam-4669608.html), [SCMP](https://amp.scmp.com/news/hong-kong/hong-kong-economy/article/3239501/hong-kongs-eased-visas-rules-vietnamese-first-step-more-travel-relaxations-and-open-access-inflow).

### Chưa biết (HK1 phải trả lời)
1. Đại lý của mình **mỗi tháng có bao nhiêu bộ HK**? Hiện họ làm thế nào, mất bao lâu, hay sai ở đâu? (hỏi 3–5 đại lý lớn nhất)
2. Visa thăm 1 lần có bắt buộc **người bảo lãnh ở HK** không? Giấy tờ bắt buộc từng loại (du lịch, thăm thân, công tác).
3. e-Visa có **API gọi được** (như COVA) hay chỉ là form web (captcha, đăng nhập) hay phải nộp giấy?
4. Ai đứng tên nộp: người xin visa tự nộp, hay đại lý / bên bảo lãnh nộp hộ?
5. Thời gian xử lý, lệ phí, tỉ lệ đậu ước tính.

### HK1 — Khảo sát
**Kỳ vọng**: trả lời đủ 5 câu trên, có nguồn; quyết định **làm / không làm** dựa trên số bộ/tháng × thời gian tiết kiệm.

### HK2 — Khai thử tay
**Kỳ vọng**: khai 1–3 bộ thật trên e-Visa với DevTools (F12 → Network), ghi lại: các trang form, trường, các request (có JSON API không), cách đăng nhập, upload. Ước lượng % tự động được.

### HK3 — Hồ sơ khách chuẩn hoá
**Kỳ vọng**: kiểu dữ liệu `Applicant` (người, gia đình, công việc, chuyến đi, giấy tờ đã đọc) độc lập với COVA; luồng COVA hiện tại chuyển sang dùng nó mà **snapshot test không đổi**.

### HK4 — MVP
**Kỳ vọng**: 1 loại visa HK phổ biến nhất (theo HK1), khai tự động từ cùng thư mục hồ sơ; đo thời gian khai so với khai tay.

---

## Nhật ký

| Ngày       | Việc                                                                 |
| ---------- | -------------------------------------------------------------------- |
| 2026-11-28 | Tạo file. Gửi truy vấn U1 cho người dùng chạy trên VPS. Phát hiện K3. |
| 2026-11-28 | U1 xong (98,8 % duyệt; Q là điểm yếu). K3 bỏ (logic đúng). HK tạm hoãn. Thêm K2 quy tắc 15, K7. |
| 2026-11-28 | Bỏ K2 quy tắc 15 (bằng chứng quan hệ Q vợ/chồng): để `qkhac_`, bổ sung sau được. |
| 2026-11-28 | K1 + K2 code xong (`web/file_check.js`, form `/web`), 109 test Node qua, khớp n8n. Chờ test trên hồ sơ thật. |
| 2026-11-28 | K2: ❌ tạm không chặn (hỏi xác nhận, `FC_BLOCK_ERRORS = false`); M / F thiếu giấy → ⚠️ nhắc Áp dụng M / F. |
