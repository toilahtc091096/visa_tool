import asyncio
from datetime import date
from flows import run_flow
import json


def load_case(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "register_date" not in data or data["register_date"] in (None, ""):
        data["register_date"] = date.today()
    elif isinstance(data["register_date"], str):
        y, m, d = map(int, data["register_date"].split("-"))
        data["register_date"] = date(y, m, d)

    return data

#need param
case = load_case("resources/l_info.json")
__all__ = ["run_flow", "main"]


def main() -> None:
    asyncio.run(
        run_flow(
            case["authorization"],
            # common
            case["visa_type"],
            case["register_date"],
            case["guest_name"],
            case["ticket_names"],
            case["province_city_code"],
            case["id_card_number"],
            case["entries_type"],
            case["type_of_visa_sub_value"],
            case["service_type"],
            # family
            case["haveSpouseFlag"],
            case["ct08_province_city_code"],
            case["haveChildFlag"],
            case["childFamilyName"],
            case["childGivenName"],
            case["childNationality"],
            case["childBirthDate"],
            # father
            case["fatherFamilyName"],
            case["fatherGivenName"],
            case["fatherNationality"],
            case["fatherBirthDate"],
            # mother
            case["motherFamilyName"],
            case["motherGivenName"],
            case["motherNationality"],
            case["motherBirthDate"],
            # travel info
            case["arrivedChinaFlag"],
            case["haveChinaVisaFlag"],
            case["old_visaType"],
            case["old_visaNumber"],
            case["old_issueDate"],
            case["old_issuePlace"],
            case["haveOtherVisaFlag"],
            case["old_otherVisas"],
            case["old_otherCountries"],
            # payer
            case["payMobile"],
            case["payName"],
        )
    )


if __name__ == "__main__":
    main()
 