# Bảng đối chiếu upload: Bắc ↔ Nam

Cột **Bắc** lấy từ code hiện tại (giữ nguyên). Bạn điền các cột **Nam**.
- Mỗi dòng ghi đủ **categoryCode + materialCode** (vd `mfa-130`) và các slot (vd `_1,_2`).
- Nam không có mục đó: ghi `KHÔNG` ở cột Nam: materialCode.
- Nam có mục mà Bắc không có: điền vào các dòng `(mới)` cuối mỗi bảng, ghi rõ file gì.
- Cột Nam của L30 đã điền sẵn theo code hiện tại; sửa nếu sai.

### Mẫu cách điền (chỉ là ví dụ, không thuộc bảng nào)

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang` (4)<br>`chung\xac_nhan_tu_trung_tam_visa` (1) | `12025062114211484037531` | `mfa-044 _1,2,3,4` | 其他材料 Other materials | `22025070216133602452066` | mfa-130 | _1,_2,_3 | _1 = xác nhận TT visa, _2.._3 = hộ chiếu trắng |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | | | KHÔNG | | Nam không yêu cầu |
| (mới) | Vé tàu cao tốc | `chung\ve_tau` | — | — | 火车票 Train ticket | `12025xxxxxxxxxxxxxxxxx` | mfa-0xx | _1 | Nam có, Bắc không có |


## L15

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | |  |  |  | |
| FLIGHT_TICKET | Vé máy bay | `chung\ve_may_bay` (1) | `12025062020000706552852` | `mfa-003 _1` | |  |  |  | |
| HOTEL_RESERVATION_WITH_PAYMENT | Đặt phòng khách sạn | `chung\khach_san` (1) | `12025063014542307352106` | `mfa-002 _1,2,3` | |  |  |  | |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | |  |  |  | |
| BANK_STATEMENT | Sao kê ngân hàng | `chung\sao_ke_ngan_hang` (2) | `12025062216413672273869` | `mfa-007 _1,2,3,4` | |  |  |  | |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | |  |  |  | |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang` (4)<br>`chung\xac_nhan_tu_trung_tam_visa` (1) | `12025062114211484037531` | `mfa-044 _1,2,3,4` | |  |  |  | |
| VISA_CENTER_CONFIRMATION | Xác nhận trung tâm visa | (không có config riêng) | `12025062114211484037531` | `mfa-044 _5` | |  |  |  | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | |  |  |  | |
| UNDER_18 | Giấy tờ dưới 18 tuổi | `duoi_18_tuoi\giay_to_cho_nguoi_duoi_18` (5) | `22026072917255869849620` | `mfa-039 _1,2,3,4,5` | |  |  |  | |
| OTHER_COUNTRY_VISAS | Visa nước khác | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (3) | `12025062114213765489140` | `mfa-011 _1,2,3` | |  |  |  | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |

## L30

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | | `22025062618255280352880` | mfa-079 | _1 | |
| FLIGHT_TICKET | Vé máy bay | `chung\ve_may_bay` (1) | `12025062020000706552852` | `mfa-003 _1` | | `12025062616424538491658` | mfa-088 | _1 | |
| HOTEL_RESERVATION_WITH_PAYMENT | Đặt phòng khách sạn | `chung\khach_san` (1) | `12025063014542307352106` | `mfa-002 _1,2,3` | | `12025062616431978476716` | mfa-089 | _1 | |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | |  |  |  | |
| BANK_STATEMENT | Sao kê ngân hàng | `chung\sao_ke_ngan_hang` (2) | `12025062216413672273869` | `mfa-007 _1,2,3,4` | |  |  |  | |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | | `22025062618224586258771` | mfa-097 | _1,2,3,4 | |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang` (4)<br>`chung\xac_nhan_tu_trung_tam_visa` (1) | `12025062114211484037531` | `mfa-044 _1,2,3,4` | | `22025070216133602452066` | mfa-130 | _1 | |
| VISA_CENTER_CONFIRMATION | Xác nhận trung tâm visa | (không có config riêng) | `12025062114211484037531` | `mfa-044 _5` | |  |  |  | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | | `22025062618255280352880` | mfa-079 | _2,3,4,5,6,7 | |
| UNDER_18 | Giấy tờ dưới 18 tuổi | `duoi_18_tuoi\giay_to_cho_nguoi_duoi_18` (5) | `22026072917255869849620` | `mfa-039 _1,2,3,4,5` | |  |  |  | |
| OTHER_COUNTRY_VISAS | Visa nước khác | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (3) | `12025062114213765489140` | `mfa-011 _1,2,3` | |  |  |  | |
| ITINERARY_IN_CHINA | Lịch trình tại TQ | `lich_trinh_du_lich` (1) | `12025062019595907456262` | `mfa-004 _1` | | `12025062616415987523440` | mfa-087 | _1 | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |

## M

Nam: đã code (profile `SouthBusinessVisa`, bảng file `UPLOAD_CONFIG_SOUTH_M`).

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | Passport information page / Trang thông tin Hộ Chiếu | `22025062618255280352880` | mfa-079 | _1 | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | (chung mục trang thông tin hộ chiếu) | `22025062618255280352880` | mfa-079 | _2 → _8 | Nam: visa TQ cũ (3) rồi visa nước khác (3) |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | Sổ hộ khẩu hoặc Xác nhận thông tin cư trú CT07 / CT08 | `22025062618224586258771` | mfa-097 | _1 → _4 | Nam: CT07, không có thì visa TQ cũ, không có thì visa nước khác |
| VISA_CENTER_CONFIRMATION | Xác nhận trung tâm visa | `chung\xac_nhan_tu_trung_tam_visa` (1) | `12025062114365564197636` | `mfa-053 _1` | Tài liệu bổ sung khác | `22025070216133602452066` | mfa-130 | _1 | Nam: mục "tài liệu khác" (_2 → _6 chưa dùng) |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang` (4)<br>`lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (3) | `12025062114365564197636` | `mfa-053 _2,3,4,5` | | | KHÔNG | | Nam chưa cần |
| THU_MOI | Thư mời (邀请函) | `doanh-nghiep\thu-moi` (1) | `12026072917273869111112` | `mfa-049 _1` | Thư mời / Invitation letter | `12025062617011389841743` | mfa-057 | _1, _2 | Nam lấy tối đa 2 file |
| QUYET_DINH | Quyết định cử đi | `doanh-nghiep\quyet-dinh` (1) | `12025062114271519280895` | `mfa-050 _1` | Quyết định cử đi công tác | `12025062617024509363425` | mfa-108 | _1 → _3 | Nam lấy tối đa 3 file |
| DANG_KY_DOANH_NGHIEP | Đăng ký kinh doanh | `doanh-nghiep\dangky-tq` (1) + `doanh-nghiep\dangky-vn` (1); không có thì `doanh-nghiep\dangky` (2) | `12025062114301276922307` | `mfa-051 _1,2` | | | (tách 2 dòng dưới) | | Bắc: _1 = TQ, _2 = VN |
| DANG_KY_DOANH_NGHIEP_TQ | GPKD đơn vị Trung Quốc | — | — | Bắc không có | Giấy phép kinh doanh của đơn vị Trung Quốc | `12025062617021236736326` | mfa-105 | _1 → _3 | `doanh-nghiep\dangky-tq` (3) |
| DANG_KY_DOANH_NGHIEP_VN | GPKD công ty VN | — | — | Bắc không có | Giấy phép kinh doanh công ty VN | `12025062617032656175842` | mfa-111 | _1 → _3 | `doanh-nghiep\dangky-vn` (3) |
| (mới) Hộ chiếu cũ 5 năm | Hộ chiếu cũ (trong vòng 5 năm) | — | — | Bắc không có | Old passport within five years / Hộ chiếu cũ | `22025062618250312540888` | mfa-079 | _1 → _4 | Không upload, tự up tay |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | | | KHÔNG | | |
| BANK_STATEMENT | Sao kê ngân hàng | `chung\sao_ke_ngan_hang` (2) | `12025062216413672273869` | `mfa-007 _1,2,3,4` | | | KHÔNG | | |
| UNDER_18 | Giấy tờ dưới 18 tuổi | `duoi_18_tuoi\giay_to_cho_nguoi_duoi_18` (5) | `22026072917255869849620` | `mfa-039 _1,2,3,4,5` | | | KHÔNG | | |
| OTHER_COUNTRY_VISAS | Visa nước khác | — | `12025062114213765489140` | `mfa-011 _1,2,3` | | | KHÔNG | | Nam: nằm trong mfa-079 |
| ITINERARY_IN_CHINA | Lịch trình tại TQ | `lich_trinh_du_lich` (1) | `12025062019595907456262` | `mfa-004 _1` | | | KHÔNG | | |

## Q1

Nam: đã code (profile `SouthQ1Visa`, bảng file `UPLOAD_CONFIG_SOUTH_Q1`).

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | Passport information page / Trang thông tin Hộ Chiếu | `22025062618255280352880` | mfa-079 | _1 | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1` | (chung mục trang thông tin hộ chiếu) | `22025062618255280352880` | mfa-079 | _2 → _8 | Nam: visa TQ cũ (3) rồi visa nước khác (3) |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `12025062115232232717451` | `mfa-030 _4` | Sổ hộ khẩu hoặc Xác nhận thông tin cư trú CT07 / CT08 | `22025062618224586258771` | mfa-097 | _1 → _4 | Nam: CT07, không có thì visa TQ cũ, không có thì visa nước khác |
| THU_MOI | Thư mời (邀请函) | `tham-than\thumoi` (1) | `12025062115033600751835` | `mfa-070 _1` | Thư Mời | `12025062617103405430938` | mfa-012 | _1 → _3 | Nam lấy tối đa 3 file |
| CCCD_NGUOI_MOI | CCCD người mời | `tham-than\cccd` (2) | `12025062115051305548199` | `mfa-071 _1,2` | CCCD Người mời | `12025062617162059612389` | mfa-012 | _1 → _3 | Nam lấy tối đa 3 file |
| CHUNG_MINH_QUAN_HE | Chứng minh quan hệ (关系证明) | `tham-than\quan-he` (4) | `12025062115240751955592` | `mfa-073 _1,2,3,4` | Chứng minh mối quan hệ giữa người mời và người được mời | `12025062617242615028456` | mfa-012 | _1 → _6 | Nam lấy tối đa 6 file |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`tham-than\khac` (4) | `12025062115165388661358` | `mfa-085 _1,2,3,4,5` | Tài liệu bổ sung khác | `22025070216133602452066` | mfa-130 | _1 → _6 | _1 = xác nhận TT visa, _2 → _6 = `tham-than\khac` (5) |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | | | KHÔNG | | |

## Q2

Nam: đã code (profile `SouthQ2Visa`, bảng file `UPLOAD_CONFIG_SOUTH_Q2`). Bỏ qua: "If you are a non-Vietnamese foreigner", "If you once had Chinese nationality...", "Old passport within five years".

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | Passport information page / Trang thông tin Hộ Chiếu | `22025062618255280352880` | mfa-079 | _1 | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1` | (chung mục trang thông tin hộ chiếu) | `22025062618255280352880` | mfa-079 | _2 → _8 | Nam: visa TQ cũ (3) rồi visa nước khác (3) |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `12025062115232232717451` | `mfa-030 _4` | Sổ hộ khẩu hoặc Xác nhận thông tin cư trú CT07 / CT08 | `22025062618224586258771` | mfa-097 | _1 → _4 | Nam: CT07, không có thì visa TQ cũ, không có thì visa nước khác |
| CCCD_NGUOI_MOI | CCCD người mời | `tham-than\cccd` (2) | `12025062115202108210397` | `mfa-092 _1,2` | Căn cước công dân người mời | `12025062617342103276497` | mfa-015 | _1 → _3 | Nam lấy tối đa 3 file từ `tham-than\cccd` |
| THU_MOI | Thư mời (邀请函) | `tham-than\thumoi` (1) | `12025062115191056099712` | `mfa-091 _1` | Thư mời | `12025062617423948560682` | mfa-015 | _1, _2 | Nam lấy tối đa 2 file |
| CHUNG_MINH_QUAN_HE | Chứng minh quan hệ (关系证明) | `tham-than\quan-he` (3) | `12025062115232232717451` | `mfa-094 _1,2,3` | (nằm trong mục Thư mời, nhãn 亲属关系证明) | `12025062617423948560682` | mfa-015 | _3 → _5 | Nam không có mục quan hệ riêng |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`tham-than\khac` (4) | `12025062115255295051217` | `mfa-099 _1,2,3,4,5` | Tài liệu bổ sung khác | `22025070216133602452066` | mfa-130 | _1 → _6 | _1 = xác nhận TT visa, _2 → _6 = `tham-than\khac` (5) |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | | | KHÔNG | | |

## F

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | |  |  |  | |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | |  |  |  | |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | |  |  |  | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | |  |  |  | |
| THU_MOI | Thư mời (邀请函) | `du-hoc\thu-moi` (1) | `12026072917284901619425` | `mfa-061 _1` | |  |  |  | |
| QUYET_DINH_DU_HOC | Quyết định du học | `du-hoc\quyet-dinh` (2) | `12025062114560885950076` | `mfa-062 _1` | |  |  |  | |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (2) | `12025062115000341540359` | `mfa-065 _1,2,3,4` | |  |  |  | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |

## X1

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | |  |  |  | |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | |  |  |  | |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | |  |  |  | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | |  |  |  | |
| GIAY_BAO_NHAP_HOC | Giấy báo nhập học | `du-hoc\nhap-hoc` (1) | `12025062116113060399385` | `mfa-155 _1` | |  |  |  | |
| JW | Form JW | `du-hoc\jw` (1) | `12025062116141116750122` | `mfa-164 _1` | |  |  |  | |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (2) | `12025062116171641916688` | `mfa-165 _1,2,3,4` | |  |  |  | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |

## X2

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | |  |  |  | |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | |  |  |  | |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 / xác nhận việc làm | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | |  |  |  | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1,2` | |  |  |  | |
| GIAY_BAO_NHAP_HOC | Giấy báo nhập học | `du-hoc\nhap-hoc` (1) | `12025062116191142931178` | `mfa-169 _1` | |  |  |  | |
| JW | Form JW | `du-hoc\jw` (1) | `12025062116191142931178` | `mfa-169 _2` | |  |  |  | |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_cac_nuoc_khac_anh_ho_chieu` (2) | `12025062116215851186649` | `mfa-172 _1,2,3,4` | |  |  |  | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |
| (mới) | | | — | — | | | | | |

## S2

Nam: đã code (profile `SouthS2Visa`, bảng file `UPLOAD_CONFIG_SOUTH_S2`). Bỏ qua: "If you are a non-Vietnamese foreigner", "If you once had Chinese nationality...", "Old passport within five years".

| doc_type | Giấy tờ | File lấy từ (Bắc) | Bắc: categoryCode | Bắc: material / slot | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| PASSPORT_INFO_PAGE | Trang thông tin hộ chiếu | ảnh hộ chiếu gốc | — | Bắc không có | Passport information page / Trang thông tin Hộ Chiếu | `22025062618255280352880` | mfa-079 | _1 | |
| PREV_CHINESE_VISA | Visa TQ cũ (原中国签证) | `lich_su_xuat_canh\da_tung_di_nuoc_ngoai\visa_trung_quoc_cu` (3) | `22025062114131912554297` | `mfa-033 _1` | (chung mục trang thông tin hộ chiếu) | `22025062618255280352880` | mfa-079 | _2 → _8 | Nam: visa TQ cũ (3) rồi visa nước khác (3) |
| HUKOU_OR_EMPLOYMENT_LETTER | Giấy cư trú CT07 | `lich_su_xuat_canh\chua_tung_di_ho_chieu_trang\giay_cu_tru` (1) | `22025062114073725280378` | `mfa-030 _1` | Sổ hộ khẩu hoặc Xác nhận thông tin cư trú CT07 / CT08 | `22025062618224586258771` | mfa-097 | _1 → _4 | Nam: CT07, không có thì visa TQ cũ, không có thì visa nước khác |
| CCCD_NGUOI_MOI | Hộ chiếu + thẻ cư trú người mời | `tham-than\cccd` (2) | `12025062115452102589065` | `mfa-123 _1,2` | Thẻ cư trú của người mời | `12025062617530813461597` | mfa-020 | _1 | Nam chỉ 1 slot |
| THU_MOI | Thư mời (邀请函) | `tham-than\thu-moi` (1) | `12025062115424944966353` | `mfa-122 _1` | Thư mời | `12025062617543110673775` | mfa-020 | _1 | |
| CHUNG_MINH_QUAN_HE | Chứng minh quan hệ (关系证明) | `tham-than\quan-he` (3) | `12025062115515363163065` | `mfa-125 _1,2,3` | Giấy tờ chứng minh mối quan hệ giữa người mời và người được mời | `12025062617562957535303` | mfa-020 | _1 | Nam chỉ 1 slot |
| OTHER_MATERIALS | Tài liệu khác (其他文件) | `chung\xac_nhan_tu_trung_tam_visa` (1)<br>`tham-than\khac` (4) | `12025062115571999891100` | `mfa-134 _1,2,3` | Tài liệu bổ sung khác | `22025070216133602452066` | mfa-130 | _1 → _6 | _1 = xác nhận TT visa, _2 → _6 = `tham-than\khac` (5) |
| PASSPORT_BLANK_PAGES | Trang trắng hộ chiếu (护照空白页) | `chung\2_trang_ho_chieu_trang` (2) | `22025070216180808782737` | `mfa-017 _1,2` | | | KHÔNG | | |

## Loại visa chỉ có ở miền Nam (nếu có)

| Loại visa | Giấy tờ | File gì / thư mục | Nam: label trên form | Nam: categoryCode | Nam: materialCode | Nam: slot | Ghi chú |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
