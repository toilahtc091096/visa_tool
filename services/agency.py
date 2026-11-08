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
        old_code = set_visa_registration_agency(
            record_id, agency["id"], overwrite=explicit
        )
        # Without overwrite an existing agency was kept: nothing moved.
        if not explicit and old_code:
            agency = {"id": None, "code": old_code}
        log_event(
            {
                "step": "assign_agency",
                "ok": True,
                "record_id": record_id,
                "agency_code": agency["code"],
                "previous_agency_code": old_code or "",
                "explicit": explicit,
            }
        )
        return {
            "agency_id": agency["id"],
            "agency_code": agency["code"],
            "previous_agency_code": old_code or "",
        }
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


def reassign_agency(
    agency_code: str,
    first_applyid: str = "",
    passport_number: str = "",
    agency_name: str = "",
) -> dict[str, Any]:
    """
    Move registrations to another agency (e.g. run with an old-style
    source_prefix such as "L15-HOANG VAN A", so it landed in CHUNG).

    Finds by first_applyid, or else the latest registration of the passport.
    Updates the DB, removes the row from the old agency sheet and writes it
    to the new one.
    """
    # Imported here: agency_sheets imports this module.
    from database.crud import (
        find_visa_registrations_with_agency,
        update_agency_name,
    )
    from services.agency_sheets import (
        remove_record_from_agency_sheet,
        write_agency_sheet_for_record,
    )

    code = str(agency_code or "").strip().upper()
    if not code:
        return {"ok": False, "error": "agency_code is required"}
    if REGION == REGION_NORTH:
        return {"ok": False, "error": "North records always belong to MB"}

    records = find_visa_registrations_with_agency(first_applyid, passport_number)
    if not records:
        return {"ok": False, "error": "registration not found"}

    agency = get_or_create_agency(code)
    if agency_name.strip():
        update_agency_name(agency["id"], agency_name.strip())

    moved: list[dict[str, Any]] = []
    for record in records:
        old_code = record.get("agency_code") or ""
        set_visa_registration_agency(record["id"], agency["id"], overwrite=True)
        item: dict[str, Any] = {
            "record_id": record["id"],
            "first_applyid": record.get("first_applyid") or "",
            "passport_number": record.get("passport_number") or "",
            "from": old_code,
            "to": agency["code"],
        }
        try:
            if old_code and old_code != agency["code"]:
                item["removed_rows"] = remove_record_from_agency_sheet(
                    old_code, item["first_applyid"]
                )
            item["sheet"] = write_agency_sheet_for_record(record["id"])
        except Exception as exc:
            item["sheet_error"] = f"{type(exc).__name__}: {exc}"
        moved.append(item)

    log_event({"step": "reassign_agency", "agency_code": agency["code"], "moved": moved})
    return {"ok": True, "agency_code": agency["code"], "moved": moved}
