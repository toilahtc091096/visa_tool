import asyncio
from datetime import date
import unicodedata
from typing import Any

from flows import run_flow
from utils import load_authorization

DEFAULT_CASE: dict[str, Any] = {
    "authorization": "",
    "first_applyid": "",
    "is_update_info": False,
    "upload_config_keys": [],
    "province_city_code": "",
    "id_card_number": "",
    "passportNumber": "",
    "register_date": "",
    "visa_type": "L15",
    "passport_type_code": "P",
    "entries_type": "S",
    "type_of_visa_sub_value": "I",
    "service_type": "N",
    "arrivedChinaFlag": False,
    "ct08_province_city_code": "",
    "haveChinaVisaFlag": False,
    "old_visaType": "",
    "old_visaNumber": "",
    "old_issueDate": "",
    "old_issuePlace": "",
    "haveOtherVisaFlag": False,
    "old_otherVisas": [],
    "old_otherCountries": [],
    "guest_name": [],
    "ticket_names": [],
    "haveSpouseFlag": False,
    "haveChildFlag": False,
    "childFamilyName": "",
    "childGivenName": "",
    "childNationality": "",
    "childBirthDate": "",
    "fatherFamilyName": "",
    "fatherGivenName": "",
    "fatherNationality": "",
    "fatherBirthDate": "",
    "motherFamilyName": "",
    "motherGivenName": "",
    "motherNationality": "",
    "motherBirthDate": "",
    "familyName": "",
    "firstName": "",
    "nationalityCountry": "",
    "birthday": "",
    "birthCountry": "",
    "birthCity": "",
    "payName": "",
    "payMobile": "",
    "chinaResidenceLicenseFlag": False,
    "collectFingerprintFlag": False,
    "is_private": False,
}


def _normalize_register_date(value: Any) -> date:
    if value in (None, ""):
        return date.today()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        y, m, d = map(int, value.split("-"))
        return date(y, m, d)
    return date.today()


def _normalize_province_city_code(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _normalize_upload_config_keys(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []
    return [str(item).strip().upper() for item in items if str(item).strip()]


def build_case(case: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(DEFAULT_CASE)
    if case:
        merged.update(case)
    merged["register_date"] = _normalize_register_date(merged.get("register_date"))
    merged["province_city_code"] = _normalize_province_city_code(
        merged.get("province_city_code")
    )
    merged["ct08_province_city_code"] = _normalize_province_city_code(
        merged.get("ct08_province_city_code")
    )
    merged["is_update_info"] = _normalize_bool(merged.get("is_update_info"))
    merged["upload_config_keys"] = _normalize_upload_config_keys(
        merged.get("upload_config_keys")
    )
    return merged


__all__ = ["run_flow", "main", "build_case", "DEFAULT_CASE"]


def main(
    case: dict[str, Any] | None = None,
    first_applyid: str | None = None,
    is_update_info: bool | None = None,
    upload_config_keys: list[str] | None = None,
) -> None:
    data = build_case(case)
    if not str(data.get("authorization", "") or "").strip():
        data["authorization"] = load_authorization()
    if first_applyid is not None:
        data["first_applyid"] = str(first_applyid).strip()
    if is_update_info is not None:
        data["is_update_info"] = _normalize_bool(is_update_info)
    if upload_config_keys is not None:
        data["upload_config_keys"] = _normalize_upload_config_keys(upload_config_keys)
    asyncio.run(
        run_flow(
            data["authorization"],
            data["visa_type"],
            data["passport_type_code"],
            data["register_date"],
            data["guest_name"],
            data["ticket_names"],
            data["province_city_code"],
            data["id_card_number"],
            data["passportNumber"],
            data["entries_type"],
            data["type_of_visa_sub_value"],
            data["service_type"],
            data["haveSpouseFlag"],
            data["ct08_province_city_code"],
            data["haveChildFlag"],
            data["childFamilyName"],
            data["childGivenName"],
            data["childNationality"],
            data["childBirthDate"],
            data["fatherFamilyName"],
            data["fatherGivenName"],
            data["fatherNationality"],
            data["fatherBirthDate"],
            data["motherFamilyName"],
            data["motherGivenName"],
            data["motherNationality"],
            data["motherBirthDate"],
            data["arrivedChinaFlag"],
            data["haveChinaVisaFlag"],
            data["old_visaType"],
            data["old_visaNumber"],
            data["old_issueDate"],
            data["old_issuePlace"],
            data["haveOtherVisaFlag"],
            data["old_otherVisas"],
            data["old_otherCountries"],
            data["familyName"],
            data["firstName"],
            data["nationalityCountry"],
            data["birthday"],
            data["birthCountry"],
            data["birthCity"],
            data["payMobile"],
            data["payName"],
            data["first_applyid"],
            data["is_update_info"],
            data["upload_config_keys"],
            data.get("chinaResidenceLicenseFlag", False),
            data.get("collectFingerprintFlag", False),
            data["is_private"],
        )
    )


if __name__ == "__main__":
    main()
