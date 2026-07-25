import asyncio
from datetime import date
import unicodedata
from typing import Any

from flows import run_flow
from flows.flow_step.common import normalize_visa_type
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
    "arrivalDate": "",
    "departureDate": "",
    "fixed_arrived": "",
    "fixed_departure": "",
    "inviteCompanyName": "",
    "company_address": "",
    "inviteProvince": "",
    "companyNameVi": "",
    "companyAddressUpperNoAccent": "",
    "companyPhone": "",
    "managerName": "",
    "work_from": "",
    "work_to": "",
    "employer_name": "",
    "employer_address": "",
    "employer_phone": "",
    "supervisor_name": "",
    "supervisor_mobile": "",
    "position": "",
    "duty": "",
    "name_of_institute": "",
    "diploma_degree": "",
    "major": "",
    "company_passport": "",
    "family_passport": "",
    "passengers": [],
    "arrivalCity": "",
    "arrivalDistrict": "",
    "stayCity": "",
    "stayDistrict": "",
    "departureCity": "",
    "departureDistrict": "",
    "passport_type_code": "P",
    "entries_type": "S",
    "type_of_visa_sub_value": "I",
    "service_type": "N",
    "visa_duration": "",
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
    "addition_adults": [],
    "addition_child": [],
    "children": [],
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


def _normalize_name_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def _normalize_children_list(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    if isinstance(value, dict):
        items = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []

    children: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        child_family = str(
            item.get("childFamilyName", item.get("familyName", "")) or ""
        ).strip()
        child_given = str(
            item.get("childGivenName", item.get("firstName", "")) or ""
        ).strip()
        child_nationality = str(
            item.get("childNationality", item.get("nationalityCountry", "")) or ""
        ).strip()
        child_birth_date = str(
            item.get("childBirthDate", item.get("birthday", "")) or ""
        ).strip()
        if not any([child_family, child_given, child_nationality, child_birth_date]):
            continue
        children.append(
            {
                "childFamilyName": child_family,
                "childGivenName": child_given,
                "childNationality": child_nationality,
                "childBirthDate": child_birth_date,
            }
        )
    return children


def build_case(case: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(DEFAULT_CASE)
    if case:
        merged.update(case)
    raw_visa_type = str(merged.get("visa_type", "") or "").strip().upper()
    raw_visa_duration = str(merged.get("visa_duration", "") or "").strip().upper()
    visa_type, visa_duration = normalize_visa_type(
        raw_visa_type,
        raw_visa_duration,
    )
    merged["visa_type_raw"] = raw_visa_type
    merged["visa_type"] = raw_visa_type or merged.get("visa_type", "")
    merged["visa_duration"] = raw_visa_duration or visa_duration
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
    merged["children"] = _normalize_children_list(merged.get("children"))
    if merged["children"]:
        first_child = merged["children"][0]
        if not str(merged.get("childFamilyName", "") or "").strip():
            merged["childFamilyName"] = first_child.get("childFamilyName", "")
        if not str(merged.get("childGivenName", "") or "").strip():
            merged["childGivenName"] = first_child.get("childGivenName", "")
        if not str(merged.get("childNationality", "") or "").strip():
            merged["childNationality"] = first_child.get("childNationality", "")
        if not str(merged.get("childBirthDate", "") or "").strip():
            merged["childBirthDate"] = first_child.get("childBirthDate", "")
        merged["haveChildFlag"] = True
    elif any(
        str(merged.get(key, "") or "").strip()
        for key in (
            "childFamilyName",
            "childGivenName",
            "childNationality",
            "childBirthDate",
        )
    ):
        merged["children"] = [
            {
                "childFamilyName": str(merged.get("childFamilyName", "") or "").strip(),
                "childGivenName": str(merged.get("childGivenName", "") or "").strip(),
                "childNationality": str(merged.get("childNationality", "") or "").strip(),
                "childBirthDate": str(merged.get("childBirthDate", "") or "").strip(),
            }
        ]
        merged["haveChildFlag"] = True
    return merged


__all__ = ["run_flow", "main", "build_case", "DEFAULT_CASE"]


def main(
    case: dict[str, Any] | None = None,
    first_applyid: str | None = None,
    is_update_info: bool | None = None,
    upload_config_keys: list[str] | None = None,
    addition_adults: list[str] | None = None,
    addition_child: list[str] | None = None,
    arrivalDate: str = "",
    departureDate: str = "",
    fixed_arrived: str | None = None,
    fixed_departure: str | None = None,
    visa_duration: str = "",
    inviteCompanyName: str = "",
    company_address: str = "",
    inviteProvince: str = "",
    companyNameVi: str = "",
    companyAddressUpperNoAccent: str = "",
    companyPhone: str = "",
    managerName: str = "",
    work_from: str = "",
    work_to: str = "",
    employer_name: str = "",
    employer_address: str = "",
    employer_phone: str = "",
    supervisor_name: str = "",
    supervisor_mobile: str = "",
    position: str = "",
    duty: str = "",
    name_of_institute: str = "",
    diploma_degree: str = "",
    major: str = "",
    children: list[dict[str, Any]] | None = None,
    company_passport: str | None = None,
    family_passport: str | None = None,
    passengers: list[dict[str, Any]] | None = None,
    arrivalCity: str = "",
    arrivalDistrict: str = "",
    stayCity: str = "",
    stayDistrict: str = "",
    departureCity: str = "",
    departureDistrict: str = "",
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
    if company_passport is not None:
        data["company_passport"] = str(company_passport).strip()
    if family_passport is not None:
        data["family_passport"] = str(family_passport).strip()
    if passengers is not None:
        data["passengers"] = list(passengers)
    if fixed_arrived is not None:
        data["fixed_arrived"] = str(fixed_arrived).strip()
    if fixed_departure is not None:
        data["fixed_departure"] = str(fixed_departure).strip()
    if addition_adults is not None:
        data["addition_adults"] = _normalize_name_list(addition_adults)
    if addition_child is not None:
        data["addition_child"] = _normalize_name_list(addition_child)
    if visa_duration not in (None, ""):
        data["visa_duration"] = str(visa_duration).strip().upper()
    asyncio.run(
        run_flow(
            data["authorization"],
            data["visa_type"],
            data.get("visa_duration", ""),
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
            data["addition_adults"],
            data["addition_child"],
            data.get("chinaResidenceLicenseFlag", False),
            data.get("collectFingerprintFlag", False),
            data["is_private"],
            data["arrivalDate"],
            data["departureDate"],
            data["fixed_arrived"],
            data["fixed_departure"],
            data["inviteCompanyName"],
            data["company_address"],
            data["inviteProvince"],
            data["companyNameVi"],
            data["companyAddressUpperNoAccent"],
            data["companyPhone"],
            data["managerName"],
            data.get("work_from", ""),
            data.get("work_to", ""),
            data.get("employer_name", ""),
            data.get("employer_address", ""),
            data.get("employer_phone", ""),
            data.get("supervisor_name", ""),
            data.get("supervisor_mobile", ""),
            data.get("position", ""),
            data.get("duty", ""),
            data.get("name_of_institute", ""),
            data.get("diploma_degree", ""),
            data.get("major", ""),
            data.get("children", []),
            data["company_passport"],
            data.get("family_passport", ""),
            data.get("passengers", []),
            data["arrivalCity"],
            data["arrivalDistrict"],
            data["stayCity"],
            data["stayDistrict"],
            data["departureCity"],
            data["departureDistrict"],
        )
    )


if __name__ == "__main__":
    main()
