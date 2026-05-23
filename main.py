import asyncio
from datetime import datetime, date
from flows import run_flow

__all__ = ["run_flow", "main"]


def main() -> None:
    # Can phai dien
    token = "MTlmOWJiMmFhZjhlNTU5MjFjZmMwOGM3ZmQ1M2Y2M2U0OGM2ZDM5YTY4YzJlZTI3YTFlODdlZGE1ZGE2Y2UwMw=="
    tmp_secret = (
        "vcenter_17097129405490_55b4fcb714cecfc1b1af4a2b79afc0a2_20050095_1779526952150_2223c6e0ca292ee01c9a9de9ed1ad8fd"
    )
    province_city_code = "HAI PHONG"
    id_card_number = "031192000564"
    file_path = r"resources\passport_data.png"
    visa_type="L15"
    register_date = date(2026,5,18)
    # for api visa type
    entries_type = "S"
    type_of_visa_sub_value = "I"
    service_type = "N"
    # ==========================================
    #1
    arrivedChinaFlag=False # Đã từng đến Trung Quốc hay chưa (TRUE/FALSE)
    #2
    haveChinaVisaFlag=False # Đã có visa Trung Quốc hay chưa (TRUE/FALSE)
    old_visaType="" #L  Loại visa Trung Quốc (bắt buộc nếu haveChinaVisaFlag=True)
    old_visaNumber="" #E12345678 Số visa Trung Quốc (không bắt buộc)
    old_issueDate="" #2024-01 Ngày cấp visa Trung Quốc (không bắt buộc, định dạng YYYY-MM-DD)
    old_issuePlace="" #Hanoi Nơi cấp visa Trung Quốc (không bắt buộc)
    #3
    haveOtherVisaFlag=False # Đã có visa nước khác (không phải Trung Quốc) hay chưa (TRUE/FALSE)
    old_otherVisas=[] #["JPN","KOR"] Danh sách mã quốc gia  của các visa khác (nên có nếu haveOtherVisaFlag=True)
    #4
    old_otherCountries=[] #"THA","" Danh sách mã quốc gia  đã đi trong 12 tháng gần nhất

    #name in ticket
    guest_name = []
    ticket_names = []

    asyncio.run(
        run_flow(
            token,
            tmp_secret,
            visa_type,
            register_date,
            guest_name,
            ticket_names,
            file_path,
            province_city_code,
            id_card_number,
            entries_type,
            type_of_visa_sub_value,
            service_type,
            arrivedChinaFlag,
            haveChinaVisaFlag,
            old_visaType,
            old_visaNumber,
            old_issueDate,
            old_issuePlace,
            haveOtherVisaFlag,
            old_otherVisas,
            old_otherCountries
        )
    )


if __name__ == "__main__":
    main()