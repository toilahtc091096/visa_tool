from __future__ import annotations

import json
import os
import re
from typing import Any

import gspread
from gspread.exceptions import APIError

_SPREADSHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def extract_spreadsheet_id(spreadsheet_url: str) -> str:
    text = (spreadsheet_url or "").strip()
    if not text:
        raise ValueError("spreadsheet_url is required")

    match = _SPREADSHEET_ID_RE.search(text)
    if match:
        return match.group(1)

    if "/" not in text and len(text) >= 20:
        return text

    raise ValueError("Unable to extract spreadsheet id from spreadsheet_url")


def _load_service_account_client() -> gspread.Client:
    info = _load_service_account_info()
    if info["source"] == "file":
        return gspread.service_account(filename=info["credentials_file"])
    if info["source"] == "json":
        return gspread.service_account_from_dict(info["credentials_json"])
    raise ValueError(
        "Missing Google credentials. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def _load_service_account_info() -> dict[str, Any]:
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if credentials_file:
        with open(credentials_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "source": "file",
            "credentials_file": credentials_file,
            "credentials_json": data,
            "client_email": str(data.get("client_email", "")).strip(),
            "project_id": str(data.get("project_id", "")).strip(),
        }

    if credentials_json:
        data = json.loads(credentials_json)
        return {
            "source": "json",
            "credentials_file": "",
            "credentials_json": data,
            "client_email": str(data.get("client_email", "")).strip(),
            "project_id": str(data.get("project_id", "")).strip(),
        }

    raise ValueError(
        "Missing Google credentials. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def _get_service_account_email() -> str:
    try:
        return _load_service_account_info().get("client_email", "")
    except Exception:
        return ""


def _get_service_account_project_id() -> str:
    try:
        return _load_service_account_info().get("project_id", "")
    except Exception:
        return ""


def _describe_gspread_api_error(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    body_text = ""

    if response is not None:
        try:
            body_text = response.text or ""
        except Exception:
            body_text = ""

    if status_code == 403 or "insufficientPermissions" in body_text:
        return "403 insufficientPermissions"
    if status_code is not None:
        return f"HTTP {status_code}"
    return type(exc).__name__


def _build_permission_error_message(
    stage: str,
    spreadsheet_id: str,
    service_account_email: str,
    exc: Exception,
) -> str:
    detail = type(exc).__name__
    if isinstance(exc, APIError):
        detail = _describe_gspread_api_error(exc)
    elif getattr(exc, "response", None) is not None:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code is not None:
            detail = f"HTTP {status_code}"

    return (
        f"Google Sheets {stage} failed with {detail} for spreadsheet_id={spreadsheet_id}. "
        f"Share the sheet with {service_account_email or '<service-account-email>'}. "
        f"Exception={type(exc).__name__}: {exc}"
    )


def _normalize_rows(
    rows: list[Any],
    header: list[str] | None = None,
) -> list[list[Any]]:
    if not rows:
        return []

    first = rows[0]
    if isinstance(first, dict):
        headers = header[:] if header else list(first.keys())
        normalized: list[list[Any]] = [headers]
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("rows must be all dicts or all lists")
            normalized.append([row.get(key, "") for key in headers])
        return normalized

    if isinstance(first, list):
        normalized_rows: list[list[Any]] = []
        for row in rows:
            if not isinstance(row, list):
                raise ValueError("rows must be all dicts or all lists")
            normalized_rows.append(row)
        if header:
            return [header, *normalized_rows]
        return normalized_rows

    raise ValueError("rows must be a list of dicts or a list of lists")


def _normalize_header_name(value: Any) -> str:
    return str(value or "").strip().casefold()


def _find_sheet_header_row(
    all_values: list[list[Any]],
    expected_header: list[str],
) -> tuple[int, list[str]] | tuple[None, None]:
    expected_names = [_normalize_header_name(name) for name in expected_header]
    expected_name_set = set(expected_names)
    key_name = _normalize_header_name("first_applyid")

    best_row_idx: int | None = None
    best_row_values: list[str] | None = None
    best_match_count = 0

    for row_idx, row in enumerate(all_values, start=1):
        normalized_row = [_normalize_header_name(cell) for cell in row]
        match_count = sum(1 for cell in normalized_row if cell in expected_name_set)
        if key_name not in normalized_row or match_count == 0:
            continue

        if (
            best_row_idx is None
            or match_count > best_match_count
            or (match_count == best_match_count and row_idx < best_row_idx)
        ):
            best_row_idx = row_idx
            best_row_values = [str(cell).strip() for cell in row]
            best_match_count = match_count

    if best_row_idx is None or best_row_values is None:
        return None, None

    return best_row_idx, best_row_values


def _build_row_by_header(
    row_header: list[str],
    row_values: list[Any],
    target_header: list[str],
) -> list[Any]:
    value_by_name = {
        _normalize_header_name(name): row_values[idx]
        for idx, name in enumerate(row_header)
        if idx < len(row_values)
    }
    return [
        value_by_name.get(_normalize_header_name(name), "") for name in target_header
    ]


def write_rows_to_google_sheet(
    spreadsheet_url: str,
    rows: list[Any],
    worksheet_name: str = "",
    mode: str = "upsert",
    header: list[str] | None = None,
) -> dict[str, Any]:
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
    client = _load_service_account_client()
    service_account_email = _get_service_account_email()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = (
            spreadsheet.worksheet(worksheet_name)
            if worksheet_name
            else spreadsheet.get_worksheet(0)
        )
    except Exception as exc:
        raise PermissionError(
            _build_permission_error_message(
                "open_by_key",
                spreadsheet_id,
                service_account_email,
                exc,
            )
        ) from exc

    normalized_rows = _normalize_rows(rows, header=header)
    if not normalized_rows:
        return {
            "ok": True,
            "spreadsheet_id": spreadsheet_id,
            "worksheet": worksheet.title,
            "written_rows": 0,
            "mode": mode,
        }

    normalized_mode = (mode or "append").strip().lower()
    if normalized_mode not in {"append", "overwrite", "upsert"}:
        raise ValueError("mode must be append, overwrite or upsert")

    if normalized_mode == "overwrite":
        try:
            worksheet.clear()
            worksheet.update("A1", normalized_rows, value_input_option="RAW")
        except Exception as exc:
            raise PermissionError(
                _build_permission_error_message(
                    "overwrite",
                    spreadsheet_id,
                    service_account_email,
                    exc,
                )
            ) from exc
    elif normalized_mode == "upsert":
        try:
            all_values = worksheet.get_all_values()

            # Header nằm ở dòng 1
            input_header = [str(name).strip() for name in normalized_rows[0]]
            input_key_idx = next(
                (
                    idx
                    for idx, name in enumerate(input_header)
                    if _normalize_header_name(name) == "first_applyid"
                ),
                None,
            )
            if input_key_idx is None:
                raise ValueError("first_applyid column is required for upsert")

            sheet_header_row_idx, sheet_header_row = _find_sheet_header_row(
                all_values,
                input_header,
            )
            if sheet_header_row_idx is None or sheet_header_row is None:
                sheet_header_row_idx = 1
                sheet_header_row = input_header[:]

            sheet_key_idx = next(
                (
                    idx
                    for idx, name in enumerate(sheet_header_row)
                    if _normalize_header_name(name) == "first_applyid"
                ),
                None,
            )
            if sheet_key_idx is None:
                raise ValueError("first_applyid column is required in sheet header")

            existing: dict[str, int] = {}
            for row_idx, row in enumerate(
                all_values[sheet_header_row_idx:],
                start=sheet_header_row_idx + 1,
            ):
                if len(row) > sheet_key_idx:
                    key = str(row[sheet_key_idx]).strip()
                    if key:
                        existing[key] = row_idx

            for row in normalized_rows[1:]:
                first_applyid = str(row[input_key_idx]).strip()
                if not first_applyid:
                    continue

                ordered_row = _build_row_by_header(
                    row_header=input_header,
                    row_values=row,
                    target_header=sheet_header_row,
                )
                if first_applyid in existing:
                    row_num = existing[first_applyid]

                    worksheet.update(
                        f"A{row_num}",
                        [ordered_row],
                        value_input_option="RAW",
                    )
                else:
                    next_row = len(worksheet.get_all_values()) + 1
                    worksheet.update(
                        f"A{next_row}",
                        [ordered_row],
                        value_input_option="RAW",
                    )

        except Exception as exc:
            raise PermissionError(
                _build_permission_error_message(
                    "upsert",
                    spreadsheet_id,
                    service_account_email,
                    exc,
                )
            ) from exc
    else:
        try:
            existing_values = worksheet.get_all_values()
            is_dict_rows = isinstance(rows[0], dict)
            has_header_row = bool(header) or is_dict_rows
            if not existing_values:
                worksheet.append_rows(normalized_rows, value_input_option="RAW")
            elif has_header_row:
                worksheet.append_rows(normalized_rows[1:], value_input_option="RAW")
            else:
                worksheet.append_rows(normalized_rows, value_input_option="RAW")
        except Exception as exc:
            raise PermissionError(
                _build_permission_error_message(
                    "upsert",
                    spreadsheet_id,
                    service_account_email,
                    exc,
                )
            ) from exc

    return {
        "ok": True,
        "spreadsheet_id": spreadsheet_id,
        "worksheet": worksheet.title,
        "written_rows": (
            len(normalized_rows) - 1
            if (header is not None or isinstance(rows[0], dict))
            else len(normalized_rows)
        ),
        "mode": normalized_mode,
    }


def write_sync_summary_to_google_sheet(
    summary: dict[str, Any],
    spreadsheet_url: str,
    worksheet_name: str = "sync_draft_visa_status",
    mode: str = "upsert",
) -> dict[str, Any]:
    items = summary.get("items")
    if not isinstance(items, list):
        raise ValueError("summary.items must be a list")

    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "record_id": item.get("id", ""),
                "full_name": item.get("full_name", ""),
                "passport_number": item.get("passport_number", ""),
                "visa_type": item.get("visa_type", ""),
                "first_applyid": item.get("first_applyid", ""),
                "ok": item.get("ok", False),
                "reason": item.get("reason", ""),
                # "remote_applyid": item.get("remote_applyid", ""),
                # "remote_status": item.get("remote_status", ""),
                "internal_status": item.get("internal_status", ""),
            }
        )

    header = [
        "record_id",
        "full_name",
        "passport_number",
        "visa_type",
        "first_applyid",
        "ok",
        "reason",
        # "remote_applyid",
        # "remote_status",
        "internal_status",
    ]
    return write_rows_to_google_sheet(
        spreadsheet_url=spreadsheet_url,
        rows=rows,
        worksheet_name=worksheet_name,
        mode=mode,
        header=header,
    )


def debug_google_sheet_access(
    spreadsheet_url: str,
    worksheet_name: str = "",
) -> dict[str, Any]:
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
    service_account_info = _load_service_account_info()
    client = _load_service_account_client()

    result: dict[str, Any] = {
        "ok": False,
        "spreadsheet_id": spreadsheet_id,
        "client_email": service_account_info.get("client_email", ""),
        "project_id": service_account_info.get("project_id", ""),
        "worksheet_name": worksheet_name,
    }

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = (
            spreadsheet.worksheet(worksheet_name)
            if worksheet_name
            else spreadsheet.get_worksheet(0)
        )
        result.update(
            {
                "ok": True,
                "spreadsheet_title": spreadsheet.title,
                "worksheet_title": worksheet.title,
                "worksheet_id": worksheet.id,
            }
        )
        return result
    except Exception as exc:
        result.update(
            {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "error_detail": _build_permission_error_message(
                    "open_by_key",
                    spreadsheet_id,
                    service_account_info.get("client_email", ""),
                    exc,
                ),
            }
        )
        return result
