"""
Google Sheet v2: one worksheet per agency (đại lý gốc), named by agency code.

Turned on by env (South server only; leave unset on the North server):
    AGENCY_SHEET_ENABLED=1
    AGENCY_SHEET_URL=https://docs.google.com/spreadsheets/d/<id>/edit

Only the columns in AGENCY_SHEET_HEADER are written. Other columns people add
to a worksheet (note, approval_status, ...) are never overwritten.
Rows are matched by visa_apply_id (= first_applyid).
"""

from __future__ import annotations

import os
import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from database.crud import list_visa_registrations_with_agency
from services.agency import NORTH_AGENCY_CODE
from services.google_sheets import (
    _chunked,
    _column_number_to_letter,
    _load_service_account_client,
    _write_rows_below,
    extract_spreadsheet_id,
)

KEY_COLUMN = "visa_apply_id"
AGENCY_SHEET_HEADER = [
    "visa_apply_id",
    "agency_code",
    "agency_name",
    "name",
    "gender",
    "passport_no",
    "visa_code",
    "status",
    "sent_at",
    "visa_status_raw",
    "visa_status_vi",
    "visa_app_no",
    "reject_reason",
    "checked_at",
    "is_vip",
]

# Columns people own (never overwritten), that the server fills only when a row is
# added or the cell is still empty: "note" gets the old agency when small agencies
# are merged into CHUNG (services/agency_merge.py).
ADD_ONLY_COLUMNS = ("note",)

# Tab in the same spreadsheet listing the VIP rows of every agency tab.
VIP_SUMMARY_TITLE = "TONG HOP VIP"
VIP_SUMMARY_HEADER = [
    "STT",
    "Ngày",
    "apply_id",
    "Tên khách hàng",
    "Giới tính KH",
    "Mã HC",
    "Loại VISA",
    "Ghi chú",
]
VIP_SUMMARY_NOTE = "VIP"

# Visa classes whose code carries a sub-type digit (Q1/Q2, S1/S2, X1/X2, J1/J2).
_VISA_CLASS_WITH_SUBTYPE = re.compile(r"^([QSXJ][12])")
_VISA_CLASS_LETTERS = re.compile(r"^([A-Z]+)")

VN_TZ = timezone(timedelta(hours=7))

# applyStatus from the online application list, plus our own sync results.
VISA_STATUS_VI = {
    "待提交": "Chờ nộp (nháp)",
    "已提交": "Đã nộp",
    "待审核": "Chờ thẩm định",
    "初审中": "Đang thẩm định",
    "审核通过": "Đã duyệt",
    "审核未通过": "Bị từ chối",
    "已撤销": "Đã rút hồ sơ",
    "已取消": "Đã hủy",
    "not_found": "Chưa thấy hồ sơ trên hệ thống",
    "api_failed": "Lỗi kiểm tra, sẽ thử lại lần sau",
    "missing_passport_number": "Thiếu số hộ chiếu",
    "missing_first_applyid": "Thiếu mã hồ sơ",
}


# A passport whose row is in one of these states is not added again.
# Matched on the status / visa_status_raw / visa_status_vi columns.
BLOCKING_STATUS_TEXTS = {
    "under_review",
    "pending_review",
    "初审中",
    "待审核",
    "đang thẩm định",
    "chờ thẩm định",
    "đang chờ duyệt",
    "chờ duyệt",
    "under review",
}
BLOCKING_STATUS_COLUMNS = ("status", "visa_status_raw", "visa_status_vi")

# One writer at a time: /run (background thread) and the sync share the sheet.
_SHEET_LOCK = threading.Lock()


def is_agency_sheet_enabled() -> bool:
    value = os.getenv("AGENCY_SHEET_ENABLED", "0").strip().lower()
    return value in {"1", "true", "yes", "on"} and bool(_agency_sheet_url())


def _agency_sheet_url() -> str:
    return os.getenv("AGENCY_SHEET_URL", "").strip()


def _sync_info(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload")
    sync = payload.get("sync") if isinstance(payload, dict) else None
    return sync if isinstance(sync, dict) else {}


def _format_sent_at(value: Any) -> str:
    if not isinstance(value, datetime):
        return str(value or "")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(VN_TZ).strftime("%d/%m/%Y %H:%M:%S")


def _visa_status_raw(row: dict[str, Any], item: dict[str, Any]) -> str:
    """Status from the last successful check; else why this check found nothing."""
    apply_status = str(_sync_info(row).get("apply_status") or "").strip()
    reason = str(item.get("reason") or "").strip()
    if reason in ("", "display_only_no_api_sync") or item.get("remote_status"):
        return str(item.get("remote_status") or apply_status)
    if apply_status:
        # This check failed but an earlier one succeeded: keep that status.
        return apply_status
    if reason == "api need new token":
        return "not_found"
    if reason == "remote_api_failed":
        return "api_failed"
    return reason


# Passport sex as saved by /run (COVA code; letters accepted too).
GENDER_LABELS = {"1": "M", "2": "F", "M": "M", "F": "F"}


def _gender_label(row: dict[str, Any]) -> str:
    payload = row.get("payload")
    value = payload.get("gender") if isinstance(payload, dict) else ""
    value = str(value or "").strip().upper()
    return GENDER_LABELS.get(value, "")


def build_agency_sheet_row(
    row: dict[str, Any],
    item: dict[str, Any],
    checked_at: str,
) -> dict[str, Any]:
    matched_row = _sync_info(row).get("matched_row")
    matched_row = matched_row if isinstance(matched_row, dict) else {}
    raw = _visa_status_raw(row, item)
    return {
        "visa_apply_id": str(row.get("first_applyid") or "").strip(),
        "agency_code": str(row.get("agency_code") or ""),
        "agency_name": str(row.get("agency_name") or ""),
        "name": str(row.get("full_name") or ""),
        "gender": _gender_label(row),
        "passport_no": str(row.get("passport_number") or ""),
        "visa_code": str(row.get("visa_type") or ""),
        "status": str(row.get("status") or ""),
        "sent_at": _format_sent_at(row.get("created_at")),
        "visa_status_raw": raw,
        "visa_status_vi": VISA_STATUS_VI.get(raw, raw) if raw else "Chờ kiểm tra",
        "visa_app_no": str(row.get("application_code") or ""),
        "reject_reason": str(matched_row.get("rejectReason") or ""),
        "checked_at": checked_at,
        "is_vip": 1 if row.get("is_vip") else 0,
    }


def _is_blocking_row(values: list[Any], col_index: dict[str, int]) -> bool:
    for name in BLOCKING_STATUS_COLUMNS:
        idx = col_index[name]
        if idx < len(values):
            text = str(values[idx]).strip().casefold()
            if text in BLOCKING_STATUS_TEXTS:
                return True
    return False


def _upsert_worksheet(
    spreadsheet: Any,
    title: str,
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Update rows already in the sheet (same visa_apply_id); append the others,
    except a passport that already has a row under review / waiting for approval.
    """
    try:
        worksheet = spreadsheet.worksheet(title)
    except Exception:
        worksheet = spreadsheet.add_worksheet(
            title=title, rows=1000, cols=len(AGENCY_SHEET_HEADER) + 5
        )

    all_values = worksheet.get_all_values()
    header = [str(cell).strip() for cell in all_values[0]] if all_values else []
    if not any(header):
        header = []
    elif KEY_COLUMN not in header:
        # Row 1 is data, not a header: put the header on top (data shifts down).
        worksheet.insert_row(AGENCY_SHEET_HEADER, 1, value_input_option="RAW")
        all_values = [AGENCY_SHEET_HEADER[:], *all_values]
        header = AGENCY_SHEET_HEADER[:]

    # Add our columns that the sheet does not have yet, after the existing ones.
    add_only = [c for c in ADD_ONLY_COLUMNS if any(str(r.get(c) or "").strip() for r in rows)]
    missing = [name for name in [*AGENCY_SHEET_HEADER, *add_only] if name not in header]
    if missing:
        first = len(header) + 1
        last = first + len(missing) - 1
        if last > worksheet.col_count:
            worksheet.add_cols(last - worksheet.col_count)
        worksheet.batch_update(
            [
                {
                    "range": (
                        f"{_column_number_to_letter(first)}1:"
                        f"{_column_number_to_letter(last)}1"
                    ),
                    "values": [missing],
                }
            ],
            value_input_option="RAW",
        )
        header.extend(missing)

    col_index = {name: header.index(name) for name in AGENCY_SHEET_HEADER}
    add_only_index = {name: header.index(name) for name in add_only}
    key_idx = col_index[KEY_COLUMN]
    passport_idx = col_index["passport_no"]
    existing: dict[str, int] = {}
    blocked_passports: set[str] = set()
    for row_num, values in enumerate(all_values[1:], start=2):
        if len(values) > key_idx and str(values[key_idx]).strip():
            existing[str(values[key_idx]).strip()] = row_num
        if len(values) > passport_idx and _is_blocking_row(values, col_index):
            passport = str(values[passport_idx]).strip().upper()
            if passport:
                blocked_passports.add(passport)

    cell_updates: list[dict[str, Any]] = []
    new_rows: list[list[Any]] = []
    skipped = 0
    for row in rows:
        key = row[KEY_COLUMN]
        if not key:
            continue
        if key not in existing and (
            str(row["passport_no"]).strip().upper() in blocked_passports
        ):
            skipped += 1
            continue
        if key in existing:
            row_num = existing[key]
            for name in AGENCY_SHEET_HEADER:
                col = _column_number_to_letter(col_index[name] + 1)
                cell_updates.append(
                    {"range": f"{col}{row_num}", "values": [[row[name]]]}
                )
            current = all_values[row_num - 1] if row_num - 1 < len(all_values) else []
            for name, idx in add_only_index.items():
                value = str(row.get(name) or "").strip()
                if value and not (idx < len(current) and str(current[idx]).strip()):
                    col = _column_number_to_letter(idx + 1)
                    cell_updates.append({"range": f"{col}{row_num}", "values": [[value]]})
        else:
            values = [""] * len(header)
            for name in AGENCY_SHEET_HEADER:
                values[col_index[name]] = row[name]
            for name, idx in add_only_index.items():
                values[idx] = str(row.get(name) or "").strip()
            new_rows.append(values)

    for chunk in _chunked(cell_updates, 500):
        worksheet.batch_update(chunk, value_input_option="RAW")
    # Keep row 1 for the header even when the sheet is still empty.
    _write_rows_below(worksheet, all_values or [header], new_rows)
    return {
        "updated": len(rows) - len(new_rows) - skipped,
        "added": len(new_rows),
        "skipped_same_passport": skipped,
    }


def write_agency_sheets(summary_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Write the records of this sync run into the per-agency worksheets."""
    if not is_agency_sheet_enabled():
        return {"ok": True, "skipped": "disabled"}

    items_by_id = {
        item.get("id"): item
        for item in summary_items
        if isinstance(item, dict) and item.get("id") is not None
    }
    # Re-read from DB: the sync has just updated status/payload.
    records = list_visa_registrations_with_agency(
        list(items_by_id),
        exclude_codes=[NORTH_AGENCY_CODE],
    )
    checked_at = (
        datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    rows = [
        build_agency_sheet_row(record, items_by_id.get(record["id"], {}), checked_at)
        for record in records
    ]
    return _write_rows(rows, remove_moved=True)


def write_agency_sheet_for_record(record_id: int | None) -> dict[str, Any]:
    """Put one registration on its agency's sheet (used by /agency/reassign)."""
    if not record_id or not is_agency_sheet_enabled():
        return {"ok": True, "skipped": "disabled"}
    records = list_visa_registrations_with_agency(
        [record_id],
        exclude_codes=[NORTH_AGENCY_CODE],
    )
    # Not checked against the visa system here: checked_at stays empty.
    rows = [build_agency_sheet_row(record, {}, "") for record in records]
    return _write_rows(rows)


def _remove_moved_rows(spreadsheet: Any, agency_by_key: dict[str, str]) -> dict[str, int]:
    """
    Delete rows whose registration now belongs to another agency (re-run
    /run with a different agency code), so it is listed only in its own tab.
    """
    removed: dict[str, int] = {}
    for worksheet in spreadsheet.worksheets():
        all_values = worksheet.get_all_values()
        if not all_values:
            continue
        header = [str(cell).strip() for cell in all_values[0]]
        if KEY_COLUMN not in header:
            continue
        key_idx = header.index(KEY_COLUMN)
        row_nums = [
            row_num
            for row_num, values in enumerate(all_values[1:], start=2)
            if len(values) > key_idx
            and agency_by_key.get(str(values[key_idx]).strip(), worksheet.title)
            != worksheet.title
        ]
        # Bottom-up so the row numbers above stay valid.
        for row_num in reversed(row_nums):
            worksheet.delete_rows(row_num)
        if row_nums:
            removed[worksheet.title] = len(row_nums)
    return removed


def _write_rows(
    rows: list[dict[str, Any]],
    remove_moved: bool = False,
) -> dict[str, Any]:
    rows_by_agency: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_agency.setdefault(row["agency_code"], []).append(row)
    if not rows_by_agency:
        return {"ok": True, "written": {}}

    written: dict[str, dict[str, int]] = {}
    errors: dict[str, str] = {}
    result: dict[str, Any] = {}
    with _SHEET_LOCK:
        client = _load_service_account_client()
        spreadsheet = client.open_by_key(extract_spreadsheet_id(_agency_sheet_url()))
        if remove_moved:
            agency_by_key = {
                row[KEY_COLUMN]: row["agency_code"] for row in rows if row[KEY_COLUMN]
            }
            try:
                result["removed_moved"] = _remove_moved_rows(spreadsheet, agency_by_key)
            except Exception as exc:
                errors["remove_moved"] = f"{type(exc).__name__}: {exc}"
        for agency_code, agency_rows in sorted(rows_by_agency.items()):
            try:
                written[agency_code] = _upsert_worksheet(
                    spreadsheet, agency_code, agency_rows
                )
            except Exception as exc:
                errors[agency_code] = f"{type(exc).__name__}: {exc}"
        try:
            result["vip_summary"] = _rebuild_vip_summary(spreadsheet)
        except Exception as exc:
            errors["vip_summary"] = f"{type(exc).__name__}: {exc}"
    return {"ok": not errors, "written": written, "errors": errors, **result}


def _is_vip_value(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "vip"}


def _sent_at_sort_key(value: str) -> datetime:
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y %H:%M:%S")
    except ValueError:
        return datetime.max


def _visa_class(visa_code: str) -> str:
    """Visa class without the stay days: Q1365 -> Q1, X2150 -> X2, L30 -> L, M90 -> M."""
    code = str(visa_code or "").strip().upper()
    match = _VISA_CLASS_WITH_SUBTYPE.match(code) or _VISA_CLASS_LETTERS.match(code)
    return match.group(1) if match else code


def _vietnamese_name_order(name: str) -> str:
    """
    full_name is stored given names first, family name last (passport order):
    "TRAN HIEU NGAN NGUYEN" -> "NGUYEN TRAN HIEU NGAN" (family name first).
    """
    parts = str(name or "").split()
    if len(parts) < 2:
        return " ".join(parts)
    return " ".join([parts[-1], *parts[:-1]])


def _collect_vip_rows(value_ranges: list[dict[str, Any]]) -> list[list[str]]:
    """VIP rows (is_vip = 1) of every agency tab, oldest first, one per visa_apply_id."""
    found: dict[str, tuple[str, list[str]]] = {}
    for value_range in value_ranges:
        values = value_range.get("values") or []
        if not values:
            continue
        header = [str(cell).strip() for cell in values[0]]
        needed = ("is_vip", "passport_no", "sent_at", "visa_app_no", KEY_COLUMN)
        if any(name not in header for name in needed):
            continue
        idx = {name: header.index(name) for name in needed}
        # Older tabs may not have these columns yet: leave the cell empty.
        for name in ("name", "gender", "visa_code"):
            if name in header:
                idx[name] = header.index(name)
        for row in values[1:]:
            cell = lambda name: (
                str(row[idx[name]]).strip() if name in idx and idx[name] < len(row) else ""
            )
            if not _is_vip_value(cell("is_vip")):
                continue
            sent_at = cell("sent_at")
            key = cell(KEY_COLUMN) or f"{cell('passport_no')}|{sent_at}"
            found[key] = (
                sent_at,
                [
                    cell(KEY_COLUMN),
                    _vietnamese_name_order(cell("name")),
                    cell("gender"),
                    cell("passport_no"),
                    _visa_class(cell("visa_code")),
                    VIP_SUMMARY_NOTE,
                ],
            )
    ordered = sorted(found.values(), key=lambda item: _sent_at_sort_key(item[0]))
    # Grouped by sent date (oldest first): STT restarts at 1 for each date and
    # an empty row separates the dates.
    result: list[list[Any]] = []
    current_date: str | None = None
    number = 0
    for sent_at, row in ordered:
        day = sent_at.split(" ")[0]
        if day != current_date:
            if current_date is not None:
                result.append([""] * len(VIP_SUMMARY_HEADER))
            current_date = day
            number = 0
        number += 1
        result.append([number, day, *row])
    return result


def _rebuild_vip_summary(spreadsheet: Any) -> dict[str, int]:
    """
    Rewrite the TONG HOP VIP tab from the agency tabs (one read for all tabs).
    The tab is generated: edits made in it are replaced on the next write.
    """
    titles = [ws.title for ws in spreadsheet.worksheets() if ws.title != VIP_SUMMARY_TITLE]
    value_ranges: list[dict[str, Any]] = []
    if titles:
        quoted = ["'" + title.replace("'", "''") + "'" for title in titles]
        value_ranges = spreadsheet.values_batch_get(quoted).get("valueRanges", [])
    rows = _collect_vip_rows(value_ranges)

    try:
        worksheet = spreadsheet.worksheet(VIP_SUMMARY_TITLE)
    except Exception:
        worksheet = spreadsheet.add_worksheet(
            title=VIP_SUMMARY_TITLE, rows=max(len(rows) + 1, 100), cols=len(VIP_SUMMARY_HEADER)
        )
    values = [VIP_SUMMARY_HEADER, *rows]
    if len(values) > worksheet.row_count:
        worksheet.add_rows(len(values) - worksheet.row_count)
    # The tab was created with fewer columns before: widen it to the header.
    if len(VIP_SUMMARY_HEADER) > worksheet.col_count:
        worksheet.add_cols(len(VIP_SUMMARY_HEADER) - worksheet.col_count)
    worksheet.batch_clear([f"A1:{_column_number_to_letter(worksheet.col_count)}"])
    worksheet.update(
        values=values,
        range_name=f"A1:{_column_number_to_letter(len(VIP_SUMMARY_HEADER))}{len(values)}",
        value_input_option="RAW",
    )
    return {"vip_rows": sum(1 for row in rows if row[0] != "")}


def remove_record_from_agency_sheet(agency_code: str, visa_apply_id: str) -> int:
    """Delete the rows of this visa_apply_id from one agency worksheet."""
    visa_apply_id = str(visa_apply_id or "").strip()
    if not is_agency_sheet_enabled() or not agency_code or not visa_apply_id:
        return 0
    with _SHEET_LOCK:
        client = _load_service_account_client()
        spreadsheet = client.open_by_key(extract_spreadsheet_id(_agency_sheet_url()))
        try:
            worksheet = spreadsheet.worksheet(agency_code)
        except Exception:
            return 0
        all_values = worksheet.get_all_values()
        if not all_values or KEY_COLUMN not in all_values[0]:
            return 0
        key_idx = [str(cell).strip() for cell in all_values[0]].index(KEY_COLUMN)
        row_nums = [
            row_num
            for row_num, values in enumerate(all_values[1:], start=2)
            if len(values) > key_idx and str(values[key_idx]).strip() == visa_apply_id
        ]
        # Bottom-up so the row numbers above stay valid.
        for row_num in reversed(row_nums):
            worksheet.delete_rows(row_num)
        return len(row_nums)


def _clear_old_tab(spreadsheet: Any, title: str, moved_keys: set[str]) -> dict[str, Any]:
    """Remove the moved rows from an agency tab; delete the tab when no data row is left.
    Rows that were not moved (e.g. another house writing the same tab) keep the tab."""
    if title in (VIP_SUMMARY_TITLE,):
        return {"skipped": "protected"}
    try:
        worksheet = spreadsheet.worksheet(title)
    except Exception:
        return {"missing": True}
    all_values = worksheet.get_all_values()
    header = [str(cell).strip() for cell in all_values[0]] if all_values else []
    key_idx = header.index(KEY_COLUMN) if KEY_COLUMN in header else -1
    moved_rows: list[int] = []
    kept = 0
    for row_num, values in enumerate(all_values[1:], start=2):
        if not any(str(v).strip() for v in values):
            continue
        key = str(values[key_idx]).strip() if 0 <= key_idx < len(values) else ""
        if key and key in moved_keys:
            moved_rows.append(row_num)
        else:
            kept += 1
    if not kept:
        spreadsheet.del_worksheet(worksheet)
        return {"deleted": True, "rows": len(moved_rows)}
    for row_num in reversed(moved_rows):
        worksheet.delete_rows(row_num)
    return {"deleted": False, "removed": len(moved_rows), "kept": kept}


def move_records_to_agency_tab(
    old_code: str,
    new_code: str,
    record_ids: list[int],
    note: str,
) -> dict[str, Any]:
    """Small agency merged into another (CHUNG): its records go to the new tab with
    ``note`` (only written on new rows / empty cells), then the old tab is cleared
    and deleted when empty."""
    if not is_agency_sheet_enabled():
        return {"ok": True, "skipped": "disabled"}
    records = list_visa_registrations_with_agency(record_ids, exclude_codes=[NORTH_AGENCY_CODE])
    rows = [{**build_agency_sheet_row(record, {}, ""), "note": note} for record in records]
    result: dict[str, Any] = {}
    errors: dict[str, str] = {}
    with _SHEET_LOCK:
        client = _load_service_account_client()
        spreadsheet = client.open_by_key(extract_spreadsheet_id(_agency_sheet_url()))
        if rows:
            try:
                result["written"] = _upsert_worksheet(spreadsheet, new_code, rows)
            except Exception as exc:
                errors[new_code] = f"{type(exc).__name__}: {exc}"
        if not errors:  # never drop the old rows before they are in the new tab
            try:
                result["old_tab"] = _clear_old_tab(
                    spreadsheet, old_code, {row[KEY_COLUMN] for row in rows if row[KEY_COLUMN]}
                )
            except Exception as exc:
                errors[old_code] = f"{type(exc).__name__}: {exc}"
        try:
            result["vip_summary"] = _rebuild_vip_summary(spreadsheet)
        except Exception as exc:
            errors["vip_summary"] = f"{type(exc).__name__}: {exc}"
    return {"ok": not errors, "errors": errors, **result}
