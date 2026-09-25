"""Q visas (family visit): Q1 and Q2, invited by a relative in China."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any

from constants import Q1_THU_MOI_OUTPUT_PATH, Q2_THU_MOI_OUTPUT_PATH
from flows.flow_payloads import getL30TravelInfo
from utils import date_util

from .base import VisaProfile, register
from .documents import InvitationLetter, VisaCenterConfirmation


class FamilyVisa(VisaProfile):
    accepts_requested_dates = True
    always_self_paid = True

    @property
    def service_key(self) -> str:
        return self.code

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
        _apply_q_single_stay_overrides(
            travel_json,
            inviterFamilyName=travel.inviterFamilyName,
            inviterGivenName=travel.inviterGivenName,
            inviterIdCard=travel.inviterIdCard,
            inviterRelation=travel.inviterRelation,
            inviterAddress=travel.inviterAddress,
            inviterPhone=travel.inviterPhone,
            inviteProvince=travel.inviteProvince,
            arrivalCity=travel.arrivalCity,
            arrivalDistrict=travel.arrivalDistrict,
            stayCity=travel.stayCity,
            stayDistrict=travel.stayDistrict,
            departureCity=travel.departureCity,
            departureDistrict=travel.departureDistrict,
            apply_visa_validity=travel.apply_visa_validity,
        )
        return travel_json


@register
class Q1Visa(FamilyVisa):
    """Family reunion / long stay with relatives living in China."""

    code = "Q1"
    documents = (VisaCenterConfirmation(), InvitationLetter(Q1_THU_MOI_OUTPUT_PATH))


@register
class Q2Visa(FamilyVisa):
    """Short visit to relatives living in China."""

    code = "Q2"
    documents = (VisaCenterConfirmation(), InvitationLetter(Q2_THU_MOI_OUTPUT_PATH))


def _add_months_to_date(source_date: date, months: int) -> date:
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _apply_q_single_stay_overrides(
    travel_json: dict[str, Any],
    *,
    inviterFamilyName: str = "",
    inviterGivenName: str = "",
    inviterIdCard: str = "",
    inviterRelation: str = "",
    inviterAddress: str = "",
    inviterPhone: str = "",
    inviteProvince: str = "",
    arrivalCity: str = "",
    arrivalDistrict: str = "",
    stayCity: str = "",
    stayDistrict: str = "",
    departureCity: str = "",
    departureDistrict: str = "",
    apply_visa_validity: Any | None = None,
) -> None:
    """
    Q-specific travel override.

    This is intentionally separate from the M helper so Q can be customized
    independently later.
    """
    invite_person = " ".join(
        part
        for part in [
            str(inviterFamilyName or "").strip(),
            str(inviterGivenName or "").strip(),
        ]
        if part
    ).strip()

    today = date.today()
    arrival_date = _add_months_to_date(today, 1)
    try:
        validity_months = int(str(apply_visa_validity or "").strip() or "6")
    except (TypeError, ValueError):
        validity_months = 6
    departure_date = _add_months_to_date(arrival_date, validity_months)

    arrival_date_str = date_util.iso_date_str(arrival_date)
    departure_date_str = date_util.iso_date_str(departure_date)
    invite_addr = str(inviterAddress or "").strip()
    arrival_city = str(arrivalCity or "").strip()
    arrival_county = str(arrivalDistrict or "").strip()
    stay_city = str(stayCity or arrivalCity or "").strip()
    stay_county = str(stayDistrict or arrivalDistrict or "").strip()
    departure_city = str(departureCity or "").strip()
    departure_county = str(departureDistrict or "").strip()
    invite_province = str(inviteProvince or "").strip()

    travel_json.update(
        {
            "inviteName": invite_person,
            "inviteCompanyName": invite_person,
            "inviteRelation": str(inviterRelation or "").strip(),
            "invitePhoneNumber": str(inviterPhone or "").strip(),
            "inviteProvince": invite_province,
            "inviteCity": arrival_city,
            "inviteCounty": arrival_county,
            "arrivalDate": arrival_date_str,
            "arrivalCityDate": arrival_date_str,
            "arrivalVehicleType": travel_json.get("arrivalVehicleType", ""),
            "arrivalCity": arrival_city,
            "arrivalCounty": arrival_county,
            "leaveDate": departure_date_str,
            "leaveVehicleType": travel_json.get("leaveVehicleType", ""),
            "leaveCity": departure_city or arrival_city,
            "leaveCounty": departure_county or arrival_county,
            "departureCity": departure_city or arrival_city,
            "departureCounty": departure_county or arrival_county,
            "travelAddr": invite_addr,
            "stayCity": stay_city,
            "stayCounty": stay_county,
            "stayDistrict": stay_county,
            "departureDistrict": departure_county or arrival_county,
        }
    )

    travel_json["stayInfo"] = [
        {
            "sort": 1,
            "stayCity": stay_city or arrival_city,
            "stayCounty": stay_county or arrival_county,
            "travelAddr": invite_addr,
            "arrivalDate": arrival_date_str,
            "leaveDate": departure_date_str,
        }
    ]

    if inviterIdCard:
        travel_json["inviterIdCard"] = str(inviterIdCard).strip()
