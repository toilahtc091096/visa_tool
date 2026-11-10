"""M visa (business): invited by a company given in the request."""

from __future__ import annotations

from datetime import date
from typing import Any

from constants import REGION, REGION_SOUTH, TRAVEL_PAY_FOR_ORGANIZATION
from flows.flow_payloads import _normalize_ascii_upper, getL30TravelInfo
from utils import date_util, ensure_company_doanh_nghiep_downloaded

from .base import ReuseRule, VisaProfile, china_place_from_pinyin, register
from .documents import CV_DOC_FOLDERS, VisaCenterConfirmation

COMPANY_REUSE = ReuseRule(
    source_field="company_passport",
    folders=CV_DOC_FOLDERS,
    missing_message="No visa center confirmation found on R2 for prefix: {prefix}",
)


class BusinessVisa(VisaProfile):
    code = "M"
    service_key = "M"
    documents = (VisaCenterConfirmation(),)
    reuse = COMPANY_REUSE
    job_type_label = "Company employee"
    works_at_inviting_company = True
    manager_is_emergency_contact = True

    def prepare_resources(self, ctx) -> None:
        company_passport = str(getattr(ctx, "company_passport", "")).strip()
        print(
            f"[company_download] visa_type={ctx.visa_type} "
            f"company_passport={company_passport}"
        )
        ensure_company_doanh_nghiep_downloaded(company_passport)

    def build_travel_json(self, travel) -> dict[str, Any]:
        travel_json = getL30TravelInfo(
            **travel.emergency(),
            is_under_18=travel.is_under_18,
            haveChildFlag=travel.haveChildFlag,
            arrival_date=travel.arrival_date,
            arrivalVehicleType="",
            leaveVehicleType="",
            is_private=travel.is_private,
        )
        place = china_place_from_pinyin(travel)
        _apply_m90_single_stay_overrides(
            travel_json,
            inviteCompanyName=travel.inviteCompanyName,
            company_address=travel.company_address,
            inviteCompanyPhone=travel.inviteCompanyPhone,
            # Request zip code first, then the district postcode.
            inviteZipCode=travel.inviteZipCode or place.postcode,
            province=place.province,
            city=place.city,
            county=place.county,
            arrivalDate=travel.arrival_date,
            departureDate=travel.leave_date,
        )
        return travel_json


class SouthBusinessVisa(BusinessVisa):
    """South (HCMC) M: same flow as the North M, plus the Vietnamese company
    as the payer. With employer_name in the request, the work info is a
    "Company employee" experience at that employer (begin date from
    date_util.work_experience_begin_date). Its upload table is
    UPLOAD_CONFIG_SOUTH_M."""

    south_employer_work = True

    def finalize_travel_json(self, travel_json: dict[str, Any], travel) -> None:
        # The applicant's company (companyNameVi) pays for the trip.
        company_name = _normalize_ascii_upper(travel.companyNameVi)
        if not company_name:
            return
        travel_json.update(
            {
                "payForTravel": TRAVEL_PAY_FOR_ORGANIZATION,
                "payForTravelName": "",
                "payForTravelPhoneNumber": "",
                "payForTravelEmail": "",
                "payForTravelOrganizationName": company_name,
                "payForTravelRelation": "CONG TY",
                "payForTravelAddr": _normalize_ascii_upper(
                    travel.companyAddressUpperNoAccent
                ),
                "payForTravelCountry": "VNM",
            }
        )


register(SouthBusinessVisa if REGION == REGION_SOUTH else BusinessVisa)


def _apply_m90_single_stay_overrides(
    travel_json: dict[str, Any],
    *,
    inviteCompanyName: str = "",
    company_address: str = "",
    inviteCompanyPhone: str = "",
    inviteZipCode: str = "",
    province: str = "",
    city: str = "",
    county: str = "",
    arrivalDate: date | str | None = None,
    departureDate: date | str | None = None,
) -> None:
    travel_address = company_address or inviteCompanyName
    arrival_date_str = (
        date_util.iso_date_str(arrivalDate)
        if isinstance(arrivalDate, date)
        else str(arrivalDate).strip() if arrivalDate is not None else ""
    )
    departure_date_str = (
        date_util.iso_date_str(departureDate)
        if isinstance(departureDate, date)
        else str(departureDate).strip() if departureDate is not None else ""
    )
    travel_json.update(
        {
            "inviteCompanyName": inviteCompanyName,
            "inviteCity": city or travel_json.get("inviteCity", ""),
            "inviteCounty": county or travel_json.get("inviteCounty", ""),
            "inviteProvince": province or travel_json.get("inviteProvince", ""),
            "inviteName": inviteCompanyName or travel_json.get("inviteName", ""),
            "inviteRelation": (
                "PARTNER"
                if inviteCompanyName
                else travel_json.get("inviteRelation", "")
            ),
            "arrivalCity": city or travel_json.get("arrivalCity", ""),
            "arrivalCounty": county or travel_json.get("arrivalCounty", ""),
            "arrivalDistrict": county or travel_json.get("arrivalDistrict", ""),
            "stayCity": city or travel_json.get("stayCity", ""),
            "stayCounty": county or travel_json.get("stayCounty", ""),
            "stayDistrict": county or travel_json.get("stayDistrict", ""),
            "travelAddr": travel_address or travel_json.get("travelAddr", ""),
            "leaveCity": city or travel_json.get("leaveCity", ""),
            "leaveCounty": county or travel_json.get("leaveCounty", ""),
            "departureCity": city or travel_json.get("departureCity", ""),
            "departureCounty": county or travel_json.get("departureCounty", ""),
            "departureDistrict": county or travel_json.get("departureDistrict", ""),
            "arrivalDate": arrival_date_str,
            "leaveDate": departure_date_str,
            "departureDate": departure_date_str,
        }
    )
    # Inviting company's phone from the request replaces the generated one.
    invite_phone = str(inviteCompanyPhone or "").strip()
    if invite_phone:
        travel_json["invitePhoneNumber"] = invite_phone
    # inviteEmail (<invitePhoneNumber digits>@qq.cn) is set in build_travel_info_profile.
    invite_zip = str(inviteZipCode or "").strip()
    if invite_zip:
        travel_json["inviteZipCode"] = invite_zip
    travel_json["stayInfo"] = [
        {
            "sort": 1,
            "stayCity": city,
            "stayCounty": county,
            "travelAddr": travel_address or travel_json.get("travelAddr", ""),
            "arrivalDate": arrival_date_str,
            "leaveDate": departure_date_str,
        }
    ]
    if arrivalDate is not None:
        if arrival_date_str:
            travel_json["arrivalDate"] = arrival_date_str
    if departureDate is not None and departure_date_str:
        travel_json["leaveDate"] = departure_date_str
        travel_json["departureDate"] = departure_date_str
