"""M visa (business): invited by a company given in the request."""

from __future__ import annotations

from datetime import date
from typing import Any

from flows.flow_payloads import getL30TravelInfo
from utils import date_util, ensure_company_doanh_nghiep_downloaded

from .base import ReuseRule, VisaProfile, register
from .documents import CV_DOC_FOLDERS, VisaCenterConfirmation

COMPANY_REUSE = ReuseRule(
    source_field="company_passport",
    folders=CV_DOC_FOLDERS,
    missing_message="No visa center confirmation found on R2 for prefix: {prefix}",
)


@register
class BusinessVisa(VisaProfile):
    code = "M"
    service_key = "M"
    documents = (VisaCenterConfirmation(),)
    reuse = COMPANY_REUSE
    accepts_requested_dates = True
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
        _apply_m90_single_stay_overrides(
            travel_json,
            inviteCompanyName=travel.inviteCompanyName,
            company_address=travel.company_address,
            inviteProvince=travel.inviteProvince,
            arrivalCity=travel.arrivalCity,
            arrivalDistrict=travel.arrivalDistrict,
            stayCity=travel.stayCity,
            stayDistrict=travel.stayDistrict,
            departureCity=travel.departureCity,
            departureDistrict=travel.departureDistrict,
            arrivalDate=travel.arrival_date,
            departureDate=travel.leave_date,
        )
        return travel_json


def _apply_m90_single_stay_overrides(
    travel_json: dict[str, Any],
    *,
    inviteCompanyName: str = "",
    company_address: str = "",
    inviteProvince: str = "",
    arrivalCity: str = "",
    arrivalDistrict: str = "",
    stayCity: str = "",
    stayDistrict: str = "",
    departureCity: str = "",
    departureDistrict: str = "",
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
            "inviteCity": arrivalCity or travel_json.get("inviteCity", ""),
            "inviteCounty": arrivalDistrict or travel_json.get("inviteCounty", ""),
            "inviteProvince": inviteProvince or travel_json.get("inviteProvince", ""),
            "inviteName": inviteCompanyName or travel_json.get("inviteName", ""),
            "inviteRelation": (
                "DOI TAC"
                if inviteCompanyName
                else travel_json.get("inviteRelation", "")
            ),
            "arrivalCity": arrivalCity or travel_json.get("arrivalCity", ""),
            "arrivalCounty": arrivalDistrict or travel_json.get("arrivalCounty", ""),
            "arrivalDistrict": arrivalDistrict
            or travel_json.get("arrivalDistrict", ""),
            "stayCity": stayCity or arrivalCity or travel_json.get("stayCity", ""),
            "stayCounty": stayDistrict
            or arrivalDistrict
            or travel_json.get("stayCounty", ""),
            "stayDistrict": stayDistrict
            or arrivalDistrict
            or travel_json.get("stayDistrict", ""),
            "travelAddr": travel_address or travel_json.get("travelAddr", ""),
            "leaveCity": departureCity or travel_json.get("leaveCity", ""),
            "leaveCounty": departureDistrict or travel_json.get("leaveCounty", ""),
            "departureCity": departureCity or travel_json.get("departureCity", ""),
            "departureCounty": departureDistrict
            or travel_json.get("departureCounty", ""),
            "departureDistrict": departureDistrict
            or travel_json.get("departureDistrict", ""),
            "arrivalDate": arrival_date_str,
            "leaveDate": departure_date_str,
            "departureDate": departure_date_str,
        }
    )
    travel_json["stayInfo"] = [
        {
            "sort": 1,
            "stayCity": stayCity or arrivalCity,
            "stayCounty": stayDistrict or arrivalDistrict,
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
