"""Base class and registry for visa profiles.

A visa profile gathers everything that differs between visa types (codes,
travel info, documents to generate, upload table...). The flow steps only talk
to ``ctx.profile``; adding a visa type means adding one profile module.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, ClassVar, Iterator

from constants import (
    FLIGHT_TEMPLATE,
    JOB_TYPE_BY_LABEL,
    REGION,
    REGION_SOUTH,
    UPLOAD_CONFIG,
    UPLOAD_FILE_CODE_BY_VISA_TYPE,
    VISA_TYPE_VALUE,
    WEEK_SKIP_BY_TYPE,
)


@dataclass(frozen=True)
class ReuseRule:
    """Documents that can be taken from another applicant's R2 folder.

    When ``ctx.<source_field>`` is set, ``folders`` are downloaded from that
    prefix instead of being generated, and documents whose output folder is one
    of them are skipped.
    """

    source_field: str
    folders: tuple[str, ...]
    missing_message: str


@dataclass(frozen=True)
class UploadItem:
    doc_type: str
    codes: list[dict[str, str]]
    configs: list[dict[str, Any]]


class VisaProfile:
    code: ClassVar[str]
    """Normalized ``visa_type`` handled by this profile (``L15``, ``M``, ``Q1``...)."""
    service_key: ClassVar[str]
    """Key in SERVICE_VISA_TYPE / VISA_TYPE_VALUE / APPLY_VISA_VALIDITY."""

    documents: ClassVar[tuple] = ()
    """DocumentStep instances rendered, in order, after the travel info is saved."""
    reuse: ClassVar[ReuseRule | None] = None

    accepts_requested_dates: ClassVar[bool] = True
    """Use arrivalDate/departureDate from the request when both are given;
    set False on a profile that must always compute its own dates."""
    start_extra_weeks: ClassVar[int] = 0
    """Extra weeks added to the computed arrival date (not to request dates)."""
    trip_days: ClassVar[int | None] = None
    """Fixed trip length in days (arrival..departure inclusive) for computed
    dates; None keeps the default Monday-based length."""
    cleans_local_common_docs: ClassVar[bool] = False
    """Wipe the local ``chung/*`` folders before generating documents."""
    job_type_label: ClassVar[str | None] = None
    """Forced work-info job type; None picks a random preferred one."""
    works_at_inviting_company: ClassVar[bool] = False
    # South: an employer in the request (employer_name) gives a "Company
    # employee" work experience instead of the position-only remark.
    south_employer_work: ClassVar[bool] = False
    """Work experience is the company given in the request (company* fields)."""
    manager_is_emergency_contact: ClassVar[bool] = False
    always_self_paid: ClassVar[bool] = False
    cv_visa_type_number: ClassVar[str | None] = None
    """Number printed after the visa type on the CV form; None = duration."""

    @property
    def sub_types(self) -> dict[str, dict[str, int]]:
        return VISA_TYPE_VALUE.get(self.service_key, {})

    @property
    def flight_templates(self) -> list[dict[str, str]]:
        return FLIGHT_TEMPLATE.get(self.code, [])

    @property
    def week_skip(self) -> int | None:
        return WEEK_SKIP_BY_TYPE.get(self.code)

    def reuse_prefix(self, ctx) -> str:
        """Prefix to reuse documents from, or "" when nothing is reused."""
        if self.reuse is None:
            return ""
        return str(getattr(ctx, self.reuse.source_field, "") or "").strip()

    # ---- hooks ---------------------------------------------------------
    def prepare_resources(self, ctx) -> None:
        """Download type-specific input folders (company, school...) from R2."""

    def choose_hotel(self, ctx) -> None:
        """Pick the hotel used for the travel info and the hotel booking."""

    def choose_hotel_and_flight(self, ctx, has_additional_names: bool) -> None:
        self.choose_hotel(ctx)
        if self.flight_templates:
            ctx.flight_ticket = random.randrange(len(self.flight_templates))
        if ctx.is_under_18 or has_additional_names:
            ctx.flight_ticket = 0

    def build_work_info(self, ctx):
        """Return the SaveWorkInfo body (WorkInfoProfile) for ``ctx``."""
        from flows.flow_payloads import (
            build_south_work_info_without_input,
            build_work_info_profile,
        )

        from utils import log_event

        has_input = self._has_work_input(ctx)
        south_employer = (
            REGION == REGION_SOUTH
            and self.south_employer_work
            and not ctx.is_under_18
            and bool(str(getattr(ctx, "employer_name", "") or "").strip())
        )
        south_position = (
            self._south_position(ctx)
            if REGION == REGION_SOUTH and not ctx.is_under_18 and not south_employer
            else ""
        )
        log_event(
            {
                "step": "work_info_source",
                "region": REGION,
                "visa_type": self.code,
                "has_work_input": has_input,
                "is_under_18": bool(ctx.is_under_18),
                "is_retired": bool(getattr(ctx, "is_retired", False)),
                "old_item_id": getattr(ctx, "old_item_id", ""),
                "old_job_type": ctx.job_type,
                "old_experiences": len(ctx.experiences or []),
                "branch": "south_employer"
                if south_employer
                else "south_position"
                if south_position
                else "south_no_input"
                if REGION == REGION_SOUTH and not has_input
                else "default",
            }
        )
        if south_position:
            return build_south_work_info_without_input(
                ctx.first_applyid,
                JOB_TYPE_BY_LABEL["Self-employed"],
                [],
                [{"notApplyCode": "workExperience", "remark": south_position}],
            )
        if REGION == REGION_SOUTH and not has_input:
            return build_south_work_info_without_input(
                ctx.first_applyid,
                ctx.job_type,
                ctx.experiences,
                getattr(ctx, "old_work_not_apply_items", []),
            )
        return build_work_info_profile(
            ctx.first_applyid,
            ctx.register_date,
            ctx.ct08_province_city_code or ctx.province_city_code,
            JOB_TYPE_BY_LABEL["Company employee"] if south_employer else ctx.job_type,
            ctx.experiences,
            ctx.is_under_18,
            self,
            getattr(ctx, "companyNameVi", ""),
            getattr(ctx, "companyAddressUpperNoAccent", ""),
            getattr(ctx, "companyPhone", ""),
            getattr(ctx, "managerName", ""),
            getattr(ctx, "work_from", ""),
            getattr(ctx, "work_to", ""),
            getattr(ctx, "employer_name", ""),
            getattr(ctx, "employer_address", ""),
            getattr(ctx, "employer_phone", ""),
            getattr(ctx, "supervisor_name", ""),
            getattr(ctx, "supervisor_mobile", ""),
            getattr(ctx, "position", ""),
            getattr(ctx, "duty", ""),
            is_retired=getattr(ctx, "is_retired", False),
        )

    _WORK_INPUT_FIELDS: ClassVar[tuple[str, ...]] = (
        "work_from", "work_to", "employer_name", "employer_address",
        "employer_phone", "supervisor_name", "supervisor_mobile", "position", "duty",
    )

    @staticmethod
    def _south_position(ctx) -> str:
        """South: request position (else duty), upper case without accents, used
        as the remark of "no work experience" (e.g. "CONG NHAN")."""
        from flows.flow_payloads import _normalize_ascii_upper

        for key in ("position", "duty"):
            text = " ".join(_normalize_ascii_upper(str(getattr(ctx, key, "") or "")).split())
            if text:
                return text
        return ""

    def _has_work_input(self, ctx) -> bool:
        """Under 18, retired, work fields or the inviting company in the request:
        cases handled by build_work_info_profile in both regions."""
        if ctx.is_under_18 or getattr(ctx, "is_retired", False):
            return True
        if any(str(getattr(ctx, key, "") or "").strip() for key in self._WORK_INPUT_FIELDS):
            return True
        return self.works_at_inviting_company and bool(
            str(getattr(ctx, "companyNameVi", "") or "").strip()
        )

    def build_travel_json(self, travel) -> dict[str, Any]:
        """Return the SaveTravelInfo body for ``travel`` (a TravelInputs)."""
        raise NotImplementedError

    def finalize_travel_json(self, travel_json: dict[str, Any], travel) -> None:
        """Last changes to the SaveTravelInfo body, after the common payer
        logic (payName / payMobile) has run."""

    def upload_plan(self) -> Iterator[UploadItem]:
        """Material slots on COVA joined with the local folders that fill them."""
        configs = UPLOAD_CONFIG[self.code]
        region_codes = UPLOAD_FILE_CODE_BY_VISA_TYPE.get(self.code)
        if region_codes is None:
            raise RuntimeError(
                f"No COVA material codes for visa type {self.code} in "
                f"REGION={REGION}; add them to UPLOAD_FILE_CODE_{REGION.upper()}"
            )
        for group in region_codes.values():
            for doc_type, codes in group.items():
                config = configs.get(doc_type)
                if not config:
                    continue
                yield UploadItem(
                    doc_type=doc_type,
                    codes=codes,
                    configs=config if isinstance(config, list) else [config],
                )


class InviterLocationFromPinyin:
    """Mixin (put before the profile class): the inviter's place in China comes
    from inviterProvincePinyin / inviterCityPinyin / inviterDistrictPinyin.

    The request's arrivalCity / stayCity / departureCity (+ districts) are
    ignored: city and district come only from the pinyin (utils.china_location),
    and inviteZipCode from the district postcode. A level the pinyin does not
    resolve is left empty and the miss is logged. inviteProvince from the
    request is kept only when the province pinyin does not resolve.
    """

    def build_travel_json(self, travel) -> dict[str, Any]:
        from dataclasses import replace

        from utils import log_event
        from utils.china_location import resolve_china_location

        names = (
            travel.inviterProvincePinyin,
            travel.inviterCityPinyin,
            travel.inviterDistrictPinyin,
        )
        id_card = str(getattr(travel, "inviterIdCard", "") or "").strip()
        place: dict[str, str] = {}
        if any(str(n or "").strip() for n in names):
            place = resolve_china_location(*names, id_card=id_card)
            event: dict[str, Any] = {
                "step": "inviter_location",
                "pinyin": list(names),
                "resolved": place,
            }
            if "city_code" not in place:
                # City / district are sent empty: check them by hand.
                event["warning"] = "inviter city not found from pinyin"
            elif (
                "county_code" in place
                and len(id_card) >= 6
                and id_card[:6] != place["county_code"]
            ):
                # Only a note: the inviter may live away from the ID's county.
                event["note"] = f"ID card county {id_card[:6]} != {place['county_code']}"
            log_event(event)
        if "province_code" in place:
            travel = replace(travel, inviteProvince=place["province_code"])
        city = place.get("city_code", "")
        county = place.get("county_code", "")
        travel = replace(
            travel,
            arrivalCity=city,
            stayCity=city,
            departureCity=city,
            arrivalDistrict=county,
            stayDistrict=county,
            departureDistrict=county,
        )
        travel_json = super().build_travel_json(travel)
        if place.get("postcode"):
            travel_json["inviteZipCode"] = place["postcode"]
        return travel_json


_REGISTRY: dict[str, VisaProfile] = {}


def register(cls: type[VisaProfile]) -> type[VisaProfile]:
    if cls.code in _REGISTRY:
        raise ValueError(f"visa profile {cls.code!r} registered twice")
    _REGISTRY[cls.code] = cls()
    return cls


def get_visa_profile(visa_type: str) -> VisaProfile | None:
    return _REGISTRY.get(str(visa_type or "").strip().upper())


def registered_visa_types() -> list[str]:
    return sorted(_REGISTRY)


def normalize_visa_type(visa_type: str, visa_duration: str = "") -> tuple[str, str]:
    """Split a requested visa type into (profile code, duration)."""
    raw_type = str(visa_type or "").strip().upper()
    raw_duration = str(visa_duration or "").strip().upper()

    if raw_type.startswith("Q"):
        if raw_type in {"Q1", "Q2"}:
            return raw_type, raw_duration or raw_type[2:]
        if len(raw_type) > 2 and raw_type[:2] in {"Q1", "Q2"}:
            return raw_type[:2], raw_type[2:] or raw_duration
        if raw_duration:
            return raw_type, raw_duration
        return raw_type, ""

    if raw_type.startswith("M"):
        if raw_type == "M":
            if raw_duration in {"15", "30", "90", "MT", "MP", "MO"}:
                return "M", raw_duration
            return "M", "90"
        return "M", raw_type[1:] or raw_duration
    if raw_type.startswith("F"):
        if raw_type == "F":
            if raw_duration in {"15", "30", "90", "MT", "MP", "MO"}:
                return "F", raw_duration
            return "F", "15"
        return "F", raw_type[1:] or raw_duration

    if raw_type.startswith("S2"):
        # Same as Q2 for now: optional duration as "S2<days>" or visa_duration.
        return "S2", raw_type[2:] or raw_duration

    if raw_type.startswith(("X1", "X2")):
        # Study stay in days: X1 > 180 ("X1365"), X2 <= 180 ("X2150"); the
        # days may also come as visa_duration. Out of range -> no profile
        # -> "visa_type not supported".
        code = raw_type[:2]
        days = raw_type[2:] or raw_duration or ("365" if code == "X1" else "180")
        if days.isdigit():
            n = int(days)
            if (code == "X1" and n > 180) or (code == "X2" and 1 <= n <= 180):
                return code, str(n)
        return raw_type, ""

    if raw_type.startswith("L"):
        if raw_type[1:] in {"15", "30"}:
            return raw_type, raw_type[1:]
        if raw_duration in {"15", "30"}:
            return f"L{raw_duration}", raw_duration

    if raw_duration in {"15", "30", "90"}:
        return raw_type, raw_duration

    return raw_type, ""
