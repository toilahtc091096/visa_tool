import asyncio
from datetime import datetime, date
from flows import run_flow

__all__ = ["run_flow", "main"]


def main() -> None:
    # Can phai dien
    token = "NGY5YzY2ZjZmMWNhNDEyZjdkNmM2NDU3NWMxOGExYzQ1ZTgzYmViNGY0MDZhNDU1MmIyNjBhMWQwMjRjMTA5Yw=="
    tmp_secret = (
        "vcenter_17097129405490_55b4fcb714cecfc1b1af4a2b79afc0a2_62351951_1779699846513_41f2f90fed8567941a94063e485c15fd"
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
    #family
    haveSpouseFlag = True

    haveChildFlag = False
    childFamilyName = ""
    childGivenName = ""
    childNationality = ""
    childBirthDate = ""
    # parent
    # father
    fatherFamilyName = ""
    fatherGivenName = ""
    fatherNationality = ""
    fatherBirthDate = ""

    # mother
    motherFamilyName = ""
    motherGivenName = ""
    motherNationality = ""
    motherBirthDate = ""
    payMobile=""
    payName=""

    asyncio.run(
        run_flow(
            token,
            tmp_secret,
            #common
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
            #common
            #family
            haveSpouseFlag,
            haveChildFlag,
            childFamilyName, 
            childGivenName, 
            childNationality,
            childBirthDate,
            #father
            fatherFamilyName,
            fatherGivenName,
            fatherNationality,
            fatherBirthDate,
            #mother
            motherFamilyName,
            motherGivenName,
            motherNationality,
            motherBirthDate,
            #family
            #travel info
            arrivedChinaFlag,
            haveChinaVisaFlag,
            old_visaType,
            old_visaNumber,
            old_issueDate,
            old_issuePlace,
            haveOtherVisaFlag,
            old_otherVisas,
            old_otherCountries,
            payMobile,
            payName,
            #travel info
        )
    )


if __name__ == "__main__":
    main()