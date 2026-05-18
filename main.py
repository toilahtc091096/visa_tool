import asyncio
from datetime import datetime, date
from flows import run_flow

__all__ = ["run_flow", "main"]


def main() -> None:
    # Can phai dien
    base_url = (
        "https://consular.mfa.gov.cn/VISA/api/cova-service/Visa/Apply/V1" 
    )
    token = "YjI1OTg2OWIzYzhhMGM2OGI5N2I2YTRhY2VkMDQ1MDlmMWM4NDM2ZTNlNTg5MjU0OTYwYWM4YmMwOTAyY2NjYw=="
    tmp_secret = (
        "vcenter_17097129405490_55b4fcb714cecfc1b1af4a2b79afc0a2_85127832_1778984240370_53da586b25b90b2449f10cd3f97cad9e"
    )
    province_city_code = "HAI PHONG" 
    id_card_number = "031192000564" 
    file_path = r"test\passport_data.png"
    visa_type="L15"
    register_date = date(2026,5,18)
    guest_name_hotel_file = ["Hoang Thanh Cong"]
    # for api visa type
    entries_type = "S"
    type_of_visa_sub_value = "G"
    service_type = "E"
    not_previous_china = True  # True = first time in China (all flags false)
    # ==========================================


    asyncio.run(
        run_flow(
            base_url,
            token,
            tmp_secret,
            visa_type,
            register_date,
            guest_name_hotel_file,
            file_path,
            province_city_code,
            id_card_number,
            entries_type,
            type_of_visa_sub_value,
            service_type,
            not_previous_china,
        )
    )


if __name__ == "__main__":
    main()
 