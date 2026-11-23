"""South: small agencies that stopped sending records are merged into CHUNG.

An agency with fewer than SMALL_AGENCY_MAX_RECORDS records and no new record for
SMALL_AGENCY_IDLE_DAYS days: its records move to CHUNG (DB), their rows move to the
CHUNG tab with note "Từ đại lý <code> (<name>)", the old tab is deleted, the agency
row is deleted. Runs once a day on the South server (server.py), or by hand with
POST /agency/merge-small (dry_run to only list).
"""

from __future__ import annotations

import os
from typing import Any

from constants import REGION, REGION_NORTH
from database.crud.agency import (
    delete_agency_if_unused,
    get_or_create_agency,
    list_idle_small_agencies,
    move_agency_records,
)
from services.agency import DEFAULT_SOUTH_AGENCY_CODE, NORTH_AGENCY_CODE
from utils.app_logging import log_event

SMALL_AGENCY_MAX_RECORDS = 5
SMALL_AGENCY_IDLE_DAYS = 14


def is_agency_merge_enabled() -> bool:
    """South only; AGENCY_MERGE_ENABLED=0 turns the daily run off."""
    value = os.getenv("AGENCY_MERGE_ENABLED", "1").strip().lower()
    return REGION != REGION_NORTH and value in {"1", "true", "yes", "on"}


def merge_note(agency: dict[str, Any]) -> str:
    code = str(agency.get("code") or "").strip()
    name = str(agency.get("name") or "").strip()
    return f"Từ đại lý {code}" + (f" ({name})" if name and name.upper() != code.upper() else "")


def merge_small_agencies(dry_run: bool = False) -> dict[str, Any]:
    if REGION == REGION_NORTH:
        return {"ok": True, "skipped": "north"}
    # Imported here: agency_sheets imports services.agency (and the Google client).
    from services.agency_sheets import move_records_to_agency_tab

    candidates = list_idle_small_agencies(
        SMALL_AGENCY_MAX_RECORDS,
        SMALL_AGENCY_IDLE_DAYS,
        [DEFAULT_SOUTH_AGENCY_CODE, NORTH_AGENCY_CODE],
    )
    if dry_run:
        return {"ok": True, "dry_run": True, "agencies": candidates}

    target = get_or_create_agency(DEFAULT_SOUTH_AGENCY_CODE)
    merged: list[dict[str, Any]] = []
    for agency in candidates:
        item: dict[str, Any] = {"code": agency["code"], "records": agency["records"],
                                "last_record_at": agency["last_record_at"]}
        try:
            ids = move_agency_records(agency["id"], target["id"])
            item["moved_ids"] = ids
            item["sheet"] = move_records_to_agency_tab(
                agency["code"], target["code"], ids, merge_note(agency)
            )
            item["agency_deleted"] = delete_agency_if_unused(agency["id"])
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        merged.append(item)
    result = {"ok": not any("error" in m for m in merged), "to": target["code"], "merged": merged}
    log_event({"step": "merge_small_agencies", **result})
    return result
