"""Q visas (family visit): Q1 and Q2, invited by a relative in China.
S2 (foreigner's family member / personal matters) reuses the Q2 flow."""

from __future__ import annotations

import unicodedata
from calendar import monthrange
from datetime import date
from typing import Any, ClassVar

from constants import (
    Q1_THU_MOI_OUTPUT_PATH,
    Q2_THU_MOI_OUTPUT_PATH,
    REGION,
    REGION_SOUTH,
    SOUTH_INVITE_RELATION_ZH,
)
from flows.flow_payloads import form_inviter_relation, getL30TravelInfo
from utils import date_util

from .base import InviterLocationFromPinyin, VisaProfile, register
from .documents import (
    InvitationLetter,
    SouthS2InvitationLetter,
    VisaCenterConfirmation,
)


class FamilyVisa(VisaProfile):
    always_self_paid = True
    # True: leave date = arrival + visa_duration (stay days) rounded to
    # months, instead of arrival + apply_visa_validity months.
    leave_after_stay_days: ClassVar[bool] = False

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
            stay_one_year=self.code == "Q1",
            stay_days=_stay_days(travel.visa_duration)
            if self.leave_after_stay_days
            else None,
        )
        return travel_json


def _stay_days(value: Any) -> int | None:
    """visa_duration "30" -> 30; None when it is not a positive number."""
    text = str(value or "").strip()
    return int(text) if text.isdigit() and int(text) > 0 else None


class Q1Visa(FamilyVisa):
    """Family reunion / long stay with relatives living in China."""

    code = "Q1"
    cv_visa_type_number = "000"
    documents = (VisaCenterConfirmation(), InvitationLetter(Q1_THU_MOI_OUTPUT_PATH))


def _relation_key(value: str) -> str:
    """'Chồng' / 'CHONG' -> 'chong' (lowercase, no accents, single spaces)."""
    text = str(value or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.lower().split())


class SouthInviteRelationZh:
    """South Q1 / Q2: send inviteRelation in Chinese (CHONG -> 丈夫)."""

    def build_travel_json(self, travel) -> dict[str, Any]:
        travel_json = super().build_travel_json(travel)
        relation = SOUTH_INVITE_RELATION_ZH.get(
            _relation_key(travel_json.get("inviteRelation", ""))
        )
        if relation:
            travel_json["inviteRelation"] = relation
        return travel_json


SOUTH_Q_TEMPLATE = "Q_Template_MN.docx"


class SouthQ1Visa(InviterLocationFromPinyin, SouthInviteRelationZh, Q1Visa):
    """South (HCMC) Q1: same flow as the North Q1, with inviteRelation in
    Chinese, the inviter's place from pinyin and the South invitation letter.
    Its upload table is UPLOAD_CONFIG_SOUTH_Q1."""

    documents = (
        VisaCenterConfirmation(),
        InvitationLetter(Q1_THU_MOI_OUTPUT_PATH, SOUTH_Q_TEMPLATE),
    )


register(SouthQ1Visa if REGION == REGION_SOUTH else Q1Visa)


class Q2Visa(FamilyVisa):
    """Short visit to relatives living in China."""

    code = "Q2"
    documents = (VisaCenterConfirmation(), InvitationLetter(Q2_THU_MOI_OUTPUT_PATH))


class SouthQ2Visa(InviterLocationFromPinyin, SouthInviteRelationZh, Q2Visa):
    """South (HCMC) Q2: same flow as the North Q2, with inviteRelation in
    Chinese, the inviter's place from pinyin and the South invitation letter.
    Leave date = arrival + visa_duration stay days, rounded to months.
    Its upload table is UPLOAD_CONFIG_SOUTH_Q2."""

    leave_after_stay_days = True
    documents = (
        VisaCenterConfirmation(),
        InvitationLetter(Q2_THU_MOI_OUTPUT_PATH, SOUTH_Q_TEMPLATE),
    )


register(SouthQ2Visa if REGION == REGION_SOUTH else Q2Visa)


class S2Visa(FamilyVisa):
    """S2: family member of a foreigner living in China (short visit), or other
    personal matters. Same flow as Q2, but the invitation letter is not
    generated: the applicant's own letter in tham-than/thu-moi is uploaded."""

    code = "S2"
    documents = (VisaCenterConfirmation(),)


class SouthS2Visa(S2Visa):
    """South (HCMC) S2: same flow as the North S2, plus an invitation letter
    generated from S2_Template_MN.docx (used only when the applicant gave
    none). Its upload table is UPLOAD_CONFIG_SOUTH_S2."""

    documents = (VisaCenterConfirmation(), SouthS2InvitationLetter())


register(SouthS2Visa if REGION == REGION_SOUTH else S2Visa)


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
    stay_one_year: bool = False,
    stay_days: int | None = None,
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
    # Q1 (long stay, both regions): leave exactly one year after arrival (same
    # month and day; 29 Feb -> 28 Feb). South Q2: stay days rounded to months
    # (30 days = 1 month, at least 1), same day of the month: 30 -> +1 month,
    # 90 -> +3. Others: arrival + visa validity.
    if stay_days and not stay_one_year:
        months = max(1, int(stay_days / 30 + 0.5))
    else:
        months = 12 if stay_one_year else validity_months
    departure_date = _add_months_to_date(arrival_date, months)

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
            "inviteRelation": form_inviter_relation(inviterRelation),
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
