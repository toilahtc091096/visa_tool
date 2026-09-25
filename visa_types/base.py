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

    accepts_requested_dates: ClassVar[bool] = False
    """Use arrivalDate/departureDate from the request when both are given."""
    cleans_local_common_docs: ClassVar[bool] = False
    """Wipe the local ``chung/*`` folders before generating documents."""
    job_type_label: ClassVar[str | None] = None
    """Forced work-info job type; None picks a random preferred one."""
    works_at_inviting_company: ClassVar[bool] = False
    """Work experience is the company given in the request (company* fields)."""
    manager_is_emergency_contact: ClassVar[bool] = False
    always_self_paid: ClassVar[bool] = False

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

    def build_travel_json(self, travel) -> dict[str, Any]:
        """Return the SaveTravelInfo body for ``travel`` (a TravelInputs)."""
        raise NotImplementedError

    def upload_plan(self) -> Iterator[UploadItem]:
        """Material slots on COVA joined with the local folders that fill them."""
        configs = UPLOAD_CONFIG[self.code]
        for group in UPLOAD_FILE_CODE_BY_VISA_TYPE[self.code].values():
            for doc_type, codes in group.items():
                config = configs.get(doc_type)
                if not config:
                    continue
                yield UploadItem(
                    doc_type=doc_type,
                    codes=codes,
                    configs=config if isinstance(config, list) else [config],
                )


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

    if raw_type.startswith("L"):
        if raw_type[1:] in {"15", "30"}:
            return raw_type, raw_type[1:]
        if raw_duration in {"15", "30"}:
            return f"L{raw_duration}", raw_duration

    if raw_duration in {"15", "30", "90"}:
        return raw_type, raw_duration

    return raw_type, ""
