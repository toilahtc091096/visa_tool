from __future__ import annotations

from typing import Any

from constants import REGION, REGION_NORTH
from database.crud import get_or_create_agency, set_visa_registration_agency
from utils.app_logging import log_event

NORTH_AGENCY_CODE = "MB"
DEFAULT_SOUTH_AGENCY_CODE = "CHUNG"


def resolve_agency_code(payload: dict[str, Any]) -> tuple[str, bool]:
    """
    Agency code for a /run request and whether it was given explicitly.

    North: always MB. South: `agency_code` from the curl (n8n takes it from
    source_prefix), or CHUNG when missing.
    """
    if REGION == REGION_NORTH:
        return NORTH_AGENCY_CODE, True
    code = str(payload.get("agency_code", "") or "").strip().upper()
    if code:
        return code, True
    return DEFAULT_SOUTH_AGENCY_CODE, False


def assign_agency_to_registration(
    record_id: int | None,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Link the saved registration to its agency. Never raises: /run already succeeded."""
    if not record_id:
        return None
    code, explicit = resolve_agency_code(payload)
    try:
        agency = get_or_create_agency(code)
        # Without an explicit code (South re-run, no prefix code) keep the
        # agency set earlier; CHUNG only fills an empty one.
        set_visa_registration_agency(record_id, agency["id"], overwrite=explicit)
        log_event(
            {
                "step": "assign_agency",
                "ok": True,
                "record_id": record_id,
                "agency_code": agency["code"],
                "explicit": explicit,
            }
        )
        return {"agency_id": agency["id"], "agency_code": agency["code"]}
    except Exception as exc:
        log_event(
            {
                "step": "assign_agency",
                "ok": False,
                "record_id": record_id,
                "agency_code": code,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return None
