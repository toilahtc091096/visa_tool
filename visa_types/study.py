"""Study visas invited by a school given in the request: F (exchange/study),
X1 (study > 180 days) and X2 (study <= 180 days)."""

from __future__ import annotations

import unicodedata
from datetime import date
from typing import Any

from constants import DEFAULT_EMBASSY, DEFAULT_LANG, JOB_TYPE_BY_LABEL
from flows.flow_payloads import _to_dict, _work_experience_entry, getL30TravelInfo
from models import WorkInfoProfile
from utils import date_util, ensure_school_downloaded, mobile_utils

from .base import ReuseRule, VisaProfile, register
from .documents import CV_DOC_FOLDERS, VisaCenterConfirmation

SCHOOL_REUSE = ReuseRule(
    source_field="school_passport",
    folders=CV_DOC_FOLDERS,
    missing_message="No visa center confirmation found on R2 for prefix: {prefix}",
)


@register
class StudyVisa(VisaProfile):
    code = "F"
    service_key = "F"
    documents = (VisaCenterConfirmation(),)
    reuse = SCHOOL_REUSE
    job_type_label = "Student"
    academic_over_25: bool = True
    """Adults over 25 are declared as academics working at the school."""

    def prepare_resources(self, ctx) -> None:
        school_passport = str(getattr(ctx, "school_passport", "")).strip()
        print(
            f"[school_download] visa_type={ctx.visa_type} "
            f"school_passport={school_passport}"
        )
        ensure_school_downloaded(school_passport)

    def build_work_info(self, ctx) -> WorkInfoProfile:
        return build_study_work_info_profile(ctx, self.academic_over_25)

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
        _apply_f_single_stay_overrides(
            travel_json,
            inviteSchoolName=travel.inviteSchoolName,
            school_address=travel.school_address,
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


@register
class LongStudyVisa(StudyVisa):
    """X1: study longer than 180 days (365 days). Same flow as F but always a
    student; codes and uploaded school files (Admission Notice + JW201/JW202
    form) come from constants."""

    code = "X1"
    service_key = "X1"
    academic_over_25 = False
    cv_visa_type_number = "000"


@register
class ShortStudyVisa(StudyVisa):
    """X2: study up to 180 days (half a year). Same as X1."""

    code = "X2"
    service_key = "X2"
    academic_over_25 = False


def _ascii_upper(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value.upper())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def build_study_work_info_profile(ctx, academic_over_25: bool = True) -> WorkInfoProfile:
    """SaveWorkInfo body for F / X1 / X2.

    Over 25 with a school in the request (only when ``academic_over_25``):
    academic working at that school (inviteSchoolName, else name_of_institute;
    school_address). work_from, employer_*, position... from the request
    override the school defaults.
    Otherwise: student, no work experience.
    An approved previous visa (ctx.job_type / ctx.experiences, loaded in
    step 5) takes precedence over all of the above.
    """
    if ctx.job_type or ctx.experiences:
        work_end_date = date_util.work_experience_end_date()
        for experience in ctx.experiences:
            experience.endDate = work_end_date
        return _work_info_profile(
            ctx,
            ctx.job_type or JOB_TYPE_BY_LABEL["Student"],
            list(getattr(ctx, "old_work_not_apply_items", []) or []),
            [_to_dict(i) for i in ctx.experiences],
        )

    school_name = _ascii_upper(
        getattr(ctx, "inviteSchoolName", "") or getattr(ctx, "name_of_institute", "")
    )
    dob = ctx.ocr_data.Response.Data.dateOfBirth
    is_over_25 = academic_over_25 and bool(dob) and date_util.parse_date(dob) is not None and date_util.age(dob) > 25
    if not is_over_25 or not school_name:
        job_type_code = JOB_TYPE_BY_LABEL["Student"]
        not_apply_items = [{"notApplyCode": "workExperience", "remark": "CHUA DI LAM"}]
        work_experience: list[dict[str, Any]] = []
    else:
        province_city_code = ctx.ct08_province_city_code or ctx.province_city_code
        school_address = _ascii_upper(getattr(ctx, "school_address", ""))
        job_addr = (
            _ascii_upper(getattr(ctx, "employer_address", ""))
            or school_address
            or province_city_code
        )
        job_type_code = JOB_TYPE_BY_LABEL["Academic"]
        not_apply_items = []
        work_experience = [
            _work_experience_entry(
                str(getattr(ctx, "work_from", "") or "").strip()
                or date_util.work_experience_begin_date(ctx.register_date),
                str(getattr(ctx, "work_to", "") or "").strip()
                or date_util.work_experience_end_date(),
                job_addr,
                _ascii_upper(getattr(ctx, "position", "")) or "GIANG VIEN",
                _ascii_upper(getattr(ctx, "duty", "")) or "GIANG VIEN",
                job_name=_ascii_upper(getattr(ctx, "employer_name", "")) or school_name,
                job_addr=job_addr,
                job_tel=str(getattr(ctx, "employer_phone", "") or "").strip()
                or mobile_utils.generate_job_tel(),
                supervisor_name=_ascii_upper(getattr(ctx, "supervisor_name", "")),
                supervisor_tel=str(getattr(ctx, "supervisor_mobile", "") or "").strip()
                or mobile_utils.generate_supervisor_tel(),
            )
        ]

    return _work_info_profile(ctx, job_type_code, not_apply_items, work_experience)


def _work_info_profile(
    ctx,
    job_type_code: str,
    not_apply_items: list[Any],
    work_experience: list[dict[str, Any]],
) -> WorkInfoProfile:
    return WorkInfoProfile.from_dict(
        {
            "applyCountry": "",
            "finishedStep": 9,
            "embassy": DEFAULT_EMBASSY,
            "tempSaveFlag": False,
            "userId": "",
            "otherSpecify": "",
            "d3": False,
            "annualIncome": "",
            "currency": "",
            "notApplyItems": not_apply_items,
            "workExperience": work_experience,
            "applyid": ctx.first_applyid,
            "lang": DEFAULT_LANG,
            "jobType": job_type_code,
        }
    )


def _apply_f_single_stay_overrides(
    travel_json: dict[str, Any],
    *,
    inviteSchoolName: str = "",
    school_address: str = "",
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
    travel_address = school_address
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
            "inviteCompanyName": inviteSchoolName,
            "inviteCity": arrivalCity or travel_json.get("inviteCity", ""),
            "inviteCounty": arrivalDistrict or travel_json.get("inviteCounty", ""),
            "inviteProvince": inviteProvince or travel_json.get("inviteProvince", ""),
            "inviteName": inviteSchoolName or travel_json.get("inviteName", ""),
            "inviteRelation": (
                "TRUONG HOC"
                if inviteSchoolName
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
