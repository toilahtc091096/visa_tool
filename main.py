import asyncio
from datetime import datetime, date
from flows import run_flow
import random

__all__ = ["run_flow", "main"]


def main() -> None:
    # =========================
    # Case: L15 (minimal inputs)
    # =========================


    # 1) Auth (lay thu cong tu login do co captcha)
    # token = "NGY5YzY2ZjZmMWNhNDEyZjdkNmM2NDU3NWMxOGExYzQ1ZTgzYmViNGY0MDZhNDU1MmIyNjBhMWQwMjRjMTA5Ywx=="
    # tmp_secret = "vcenter_17097129405490_55b4fcb714cecfc1b1af4a2b79afc0a2_62351951_1779699846513_41f2f90fed8567941a94063e485c15fd"
    authorization = "eyJhbGciOiJIUzUxMiJ9.eyJ3ZWJzaXRlX2xvZ2luX3VzZXJfa2V5IjoiOGM0ZGRiNzItMWU0OS00Mjk2LWFiNWQtNWVhOTk5MWE5MzkzIn0.GhGd1lcXPu2CvCdtiSrUezp2PWpREWOUaCV0ookhvQbToB3MUCad899EdLqLub2dm3ASo_kfQtMZKshOJtYbZg"
    # 2) Thong tin ho so co ban
    register_date = date.today() #date(2026, 5, 27)  # Ngay dau tien dang ky

    # 3) Thong tin cu tru / dinh danh (OCR khong lay duoc tu passport -> phai nhap tay)
    province_city_code = "PHU THO"  # Tinh/TP cua nguoi nop
    id_card_number = "132471134"  # So CCCD/CMND

    # 4) Lua chon visa cho API
    visa_type = "L15"
    entries_type = "S"  # So lan nhap canh: S=Single, D=Double, M=Multiple
    type_of_visa_sub_value = "I"  # Hinh thuc nop: I=Individual, G=Group
    service_type = "N"  # Dich vu: N=Normal, E=Express

    # 5) Lich su di Trung Quoc / visa Trung Quoc
    arrivedChinaFlag = False  # Da tung den Trung Quoc chua (True/False)
    # CT08 Lay tu file CT08 va hinh anh visa cũ
    ct08_province_city_code = ""
    haveChinaVisaFlag = False  # Da tung co visa Trung Quoc chua (True/False)
    old_visaType = ""  # Loai visa Trung Quoc cu (bat buoc neu haveChinaVisaFlag=True)
    old_visaNumber = ""  # So visa Trung Quoc cu (tuy chon)
    old_issueDate = ""  # Ngay cap visa cu (tuy chon, dinh dang YYYY-MM-DD)
    old_issuePlace = random.choice(
        ["CQLXNC", "CUC QUAN LY XNC"]
    )  # Noi cap visa cu (tuy chon)

    # 6) Visa nuoc khac / lich su di nuoc khac
    haveOtherVisaFlag = False  # Da tung co visa nuoc khac (khong phai TQ) chua
    old_otherVisas = (
        []
    )  # Danh sach ma quoc gia visa nuoc khac (neu haveOtherVisaFlag=True)

    old_otherCountries = []  # Danh sach ma quoc gia da di trong 12 thang gan nhat

    # 7) Booking (khong co trong case toi gian)
    guest_name = []  # Ten khach trong booking khach san (neu co)
    ticket_names = []  # Ten hanh khach tren ve may bay (neu co)

    # 8) Thong tin nguoi than (khong co chi tiet trong case toi gian)
    haveSpouseFlag = False  # Co vo/chong (True/False) - chua co thong tin chi tiet

    haveChildFlag = False  # Co con (True/False)
    childFamilyName = ""
    childGivenName = ""
    childNationality = ""
    childBirthDate = ""

    # Cha
    fatherFamilyName = ""
    fatherGivenName = ""
    fatherNationality = ""
    fatherBirthDate = ""

    # Me
    motherFamilyName = ""
    motherGivenName = ""
    motherNationality = ""
    motherBirthDate = ""

    # 9) Nguoi tra phi (khong co trong case toi gian)
    payName = ""
    payMobile = ""

    asyncio.run(
        run_flow(
            authorization,
            # common
            visa_type,
            register_date,
            guest_name,
            ticket_names,
            province_city_code,
            id_card_number,
            entries_type,
            type_of_visa_sub_value,
            service_type,
            # family
            haveSpouseFlag,
            ct08_province_city_code,
            haveChildFlag,
            childFamilyName,
            childGivenName,
            childNationality,
            childBirthDate,
            # father
            fatherFamilyName,
            fatherGivenName,
            fatherNationality,
            fatherBirthDate,
            # mother
            motherFamilyName,
            motherGivenName,
            motherNationality,
            motherBirthDate,
            # travel info
            arrivedChinaFlag,
            haveChinaVisaFlag,
            old_visaType,
            old_visaNumber,
            old_issueDate,
            old_issuePlace,
            haveOtherVisaFlag,
            old_otherVisas,
            old_otherCountries,
            # payer
            payMobile,
            payName,
        )
    )


if __name__ == "__main__":
    main()
 