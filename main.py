import asyncio

from flows import run_flow

__all__ = ["run_flow", "main"]


def main() -> None:
    # Demo config (bạn thay bằng thật / biến môi trường)
    base_url = (
        "https://consular.mfa.gov.cn/VISA/api/cova-service/Visa/Apply/V1"
    )
    token = "YzRiYzZkNjEwZjkzNDc3MTdmZDYyYWJkMWI5YWQ2MmFmYjRlNGZiMjZmZmQ5MzhjMDBiN2Y3YTNmZDAxYjM1Ng=="
    tmp_secret = (
        "vcenter_17097129405490_55b4fcb714cecfc1b1af4a2b79afc0a2_10744952_"
        "1778767520647_6c839c86b1cb500ebf9ae528c022755a"
    )
    province_city_code = "HAI PHONG"  # lay tu api call toi
    id_card_number = "031192000564"  # lay tu api call toi
    file_path = r"D:\visa tool\KIEU_CHINH\passport_data.png"

    asyncio.run(
        run_flow(
            base_url,
            token,
            tmp_secret,
            file_path,
            province_city_code,
            id_card_number,
        )
    )


if __name__ == "__main__":
    main()
