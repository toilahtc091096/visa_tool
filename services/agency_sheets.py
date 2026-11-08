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
from datetime import datetime, timedelta, timezone
from typing import Any

from database.crud import list_visa_registrations_with_agency
from services.agency import NORTH_AGENCY_CODE
from services.google_sheets import (
    _chunked,
    _column_number_to_letter,
    _load_service_account_client,
    extract_spreadsheet_id,
)

KEY_COLUMN = "visa_apply_id"
AGENCY_SHEET_HEADER = [
    "visa_apply_id",
    "agency_code",
    "agency_name",
    "name",
    "passport_no",
    "visa_code",
    "status",
    "sent_at",
    "visa_status_raw",
    "visa_status_vi",
    "visa_app_no",
    "reject_reason",
    "checked_at",
]

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
        "passport_no": str(row.get("passport_number") or ""),
        "visa_code": str(row.get("visa_type") or ""),
        "status": str(row.get("status") or ""),
        "sent_at": _format_sent_at(row.get("created_at")),
        "visa_status_raw": raw,
        "visa_status_vi": VISA_STATUS_VI.get(raw, raw),
        "visa_app_no": str(row.get("application_code") or ""),
        "reject_reason": str(matched_row.get("rejectReason") or ""),
        "checked_at": checked_at,
    }


def _upsert_worksheet(spreadsheet: Any, title: str, rows: list[dict[str, Any]]) -> int:
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

    # Add our columns that the sheet does not have yet, after the existing ones.
    missing = [name for name in AGENCY_SHEET_HEADER if name not in header]
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
    key_idx = col_index[KEY_COLUMN]
    existing: dict[str, int] = {}
    for row_num, values in enumerate(all_values[1:], start=2):
        if len(values) > key_idx and str(values[key_idx]).strip():
            existing[str(values[key_idx]).strip()] = row_num

    cell_updates: list[dict[str, Any]] = []
    new_rows: list[list[Any]] = []
    for row in rows:
        key = row[KEY_COLUMN]
        if not key:
            continue
        if key in existing:
            row_num = existing[key]
            for name in AGENCY_SHEET_HEADER:
                col = _column_number_to_letter(col_index[name] + 1)
                cell_updates.append(
                    {"range": f"{col}{row_num}", "values": [[row[name]]]}
                )
        else:
            values = [""] * len(header)
            for name in AGENCY_SHEET_HEADER:
                values[col_index[name]] = row[name]
            new_rows.append(values)

    for chunk in _chunked(cell_updates, 500):
        worksheet.batch_update(chunk, value_input_option="RAW")
    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="RAW")
    return len(rows)


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
    rows_by_agency: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        row = build_agency_sheet_row(record, items_by_id.get(record["id"], {}), checked_at)
        rows_by_agency.setdefault(row["agency_code"], []).append(row)

    if not rows_by_agency:
        return {"ok": True, "written": {}}

    client = _load_service_account_client()
    spreadsheet = client.open_by_key(extract_spreadsheet_id(_agency_sheet_url()))
    written: dict[str, int] = {}
    errors: dict[str, str] = {}
    for agency_code, rows in sorted(rows_by_agency.items()):
        try:
            written[agency_code] = _upsert_worksheet(spreadsheet, agency_code, rows)
        except Exception as exc:
            errors[agency_code] = f"{type(exc).__name__}: {exc}"
    return {"ok": not errors, "written": written, "errors": errors}
