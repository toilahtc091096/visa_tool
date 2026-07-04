from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

from api import api_get_online_application_list_by_passport
from database.crud import (
    batch_update_visa_registration_status_and_payload,
    delete_visa_registrations_by_passport_except_status,
    list_visa_registrations_by_status,
)
from services.google_sheets import write_sync_summary_to_google_sheet
from utils import load_authorization, load_login_payload, remove_r2


DEFAULT_SYNC_STATUSES = [
    "draft",
    "under_review",
    "pending_review",
    "submitted",
    "approved",
    "rejected",
    "cancelled",
]
TERMINAL_STATUSES = {"approved", "rejected", "cancelled"}


def _extract_remote_rows(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, dict):
        rows = response.get("rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]

        data = response.get("data")
        if isinstance(data, dict):
            nested_rows = data.get("rows")
            if isinstance(nested_rows, list):
                return [row for row in nested_rows if isinstance(row, dict)]
    return []


def _extract_remote_status(row: dict[str, Any]) -> str:
    value = row.get("applyStatus")
    if value not in (None, ""):
        return str(value)
    return ""


def _map_apply_status_to_internal(apply_status: str) -> str:
    text = (apply_status or "").strip()
    if not text:
        return "draft"

    mapping = {
        "初审中": "under_review",
        "审核未通过": "rejected",
        "审核通过": "approved",
        "已撤销": "cancelled",
        "已取消": "cancelled",
        "待提交": "draft",
        "待审核": "pending_review",
        "已提交": "submitted",
    }
    if text in mapping:
        return mapping[text]

    return "unknown"


def _extract_remote_passport(row: dict[str, Any]) -> str:
    for key in ("passportNo", "passport", "passportNumber"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _extract_remote_applyid(row: dict[str, Any]) -> str:
    value = row.get("applyid")
    if value in (None, ""):
        return ""
    return str(value).strip()


def _extract_remote_application_code(row: dict[str, Any]) -> str:
    value = row.get("alFormId")
    if value in (None, ""):
        return ""
    return str(value).strip()


def _parse_statuses(statuses: str | list[str] | None) -> list[str]:
    if statuses is None:
        return DEFAULT_SYNC_STATUSES[:]
    if isinstance(statuses, str):
        parsed = [item.strip() for item in statuses.split(",")]
    else:
        parsed = [str(item).strip() for item in statuses]
    return [item for item in parsed if item]


def _build_skipped_item(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "passport_number": str(row.get("passport_number") or "").strip(),
        "first_applyid": str(row.get("first_applyid") or "").strip(),
        "ok": False,
        "reason": reason,
    }


def _build_display_only_item(row: dict[str, Any]) -> dict[str, Any]:
    internal_status = str(row.get("status") or "").strip()
    return {
        "id": row.get("id"),
        "full_name": str(row.get("full_name") or "").strip(),
        "passport_number": str(row.get("passport_number") or "").strip(),
        "visa_type": str(row.get("visa_type") or "").strip(),
        "first_applyid": str(row.get("first_applyid") or "").strip(),
        "application_code": str(row.get("application_code") or "").strip(),
        "ok": True,
        "reason": "display_only_no_api_sync",
        "remote_applyid": "",
        "remote_status": "",
        "internal_status": internal_status,
    }


def _should_sync_row_with_api(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").strip()
    application_code = str(row.get("application_code") or "").strip()
    if status == "approved":
        return not application_code
    return status not in TERMINAL_STATUSES


async def sync_draft_visa_registrations(
    page_num: int = 1,
    page_size: int = 1000,
    authorization: str = "",
    spreadsheet_url: str = "",
    worksheet_name: str = "hai",
    sheet_mode: str = "upsert",
    statuses: str | list[str] | None = None,
    max_records: int | None = None,
    concurrency: int = 5,
    skip_google_sheet: bool = False,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    print(
        "[sync_draft] start "
        f"page_num={page_num} page_size={page_size} "
        f"statuses={statuses or 'default'} max_records={max_records} "
        f"concurrency={concurrency} skip_google_sheet={skip_google_sheet}",
        flush=True,
    )

    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    tmp_secret = login_payload.get("tmpSecret", "")
    auth = authorization.strip() or load_authorization().strip() or None

    db_started_at = time.perf_counter()
    selected_statuses = _parse_statuses(statuses)
    total_rows: list[dict[str, Any]] = []
    for status in selected_statuses:
        rows = list_visa_registrations_by_status(status)
        total_rows.extend(rows)
        print(
            f"[sync_draft] loaded status={status} count={len(rows)}",
            flush=True,
        )
    if max_records is not None and max_records > 0:
        total_rows = total_rows[:max_records]
        print(
            f"[sync_draft] applied max_records={max_records} total={len(total_rows)}",
            flush=True,
        )
    print(
        "[sync_draft] db load done "
        f"total={len(total_rows)} duration={time.perf_counter() - db_started_at:.2f}s",
        flush=True,
    )

    summary: dict[str, Any] = {
        "ok": True,
        "statuses": selected_statuses,
        "api_sync_statuses": [
            status for status in selected_statuses if status not in TERMINAL_STATUSES
        ],
        "display_only_statuses": [
            status for status in selected_statuses if status in TERMINAL_STATUSES
        ],
        "total": len(total_rows),
        "draft_total": sum(1 for row in total_rows if row.get("status") == "draft"),
        "approved_missing_application_code": sum(
            1
            for row in total_rows
            if str(row.get("status") or "").strip() == "approved"
            and not str(row.get("application_code") or "").strip()
        ),
        "matched": 0,
        "updated": 0,
        "skipped": 0,
        "display_only": 0,
        "concurrency": max(1, concurrency),
        "items": [],
    }

    semaphore = asyncio.Semaphore(max(1, concurrency))
    progress_lock = asyncio.Lock()
    progress = {"done": 0, "matched": 0, "skipped": 0, "display_only": 0}

    async def process_row(
        client: httpx.AsyncClient,
        row: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        record_id = row.get("id")
        first_applyid = str(row.get("first_applyid") or "").strip()
        passport_number = str(row.get("passport_number") or "").strip()
        visa_type = str(row.get("visa_type") or "").strip()
        full_name = str(row.get("full_name") or "").strip()

        async def finish(
            item: dict[str, Any],
            update: dict[str, Any] | None,
            display_only: bool = False,
        ) -> tuple[dict[str, Any], dict[str, Any] | None]:
            async with progress_lock:
                progress["done"] += 1
                if display_only:
                    progress["display_only"] += 1
                elif update is None:
                    progress["skipped"] += 1
                else:
                    progress["matched"] += 1
                done = progress["done"]
                should_log = done == len(total_rows) or done % 10 == 0
                if should_log:
                    print(
                        "[sync_draft] api progress "
                        f"done={done}/{len(total_rows)} "
                        f"matched={progress['matched']} "
                        f"skipped={progress['skipped']} "
                        f"display_only={progress['display_only']}",
                        flush=True,
                    )
            return item, update

        if not _should_sync_row_with_api(row):
            return await finish(
                _build_display_only_item(row),
                None,
                display_only=True,
            )

        if not passport_number:
            return await finish(_build_skipped_item(row, "missing_passport_number"), None)

        if not first_applyid:
            return await finish(_build_skipped_item(row, "missing_first_applyid"), None)

        request_started_at = time.perf_counter()
        async with semaphore:
            ok, remote = await api_get_online_application_list_by_passport(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                passportNo=passport_number,
                pageNum=page_num,
                pageSize=page_size,
                authorization=auth,
            )
        request_duration = time.perf_counter() - request_started_at

        if not ok:
            print(
                "[sync_draft] remote failed "
                f"id={record_id} passport={passport_number} "
                f"duration={request_duration:.2f}s error={remote.get('error', '')}",
                flush=True,
            )
            return await finish(
                {
                    "id": record_id,
                    "passport_number": passport_number,
                    "ok": False,
                    "reason": "remote_api_failed",
                    "remote": remote,
                },
                None,
            )

        response = remote.get("response") or {}
        rows = _extract_remote_rows(response)
        matched_row = None
        for remote_row in rows:
            remote_passport = _extract_remote_passport(remote_row)
            if remote_passport != passport_number:
                continue

            remote_applyid = _extract_remote_applyid(remote_row)
            if remote_applyid == first_applyid:
                matched_row = remote_row

        if matched_row is None:
            print(
                "[sync_draft] no match "
                f"id={record_id} passport={passport_number} "
                f"first_applyid={first_applyid} rows={len(rows)} "
                f"duration={request_duration:.2f}s",
                flush=True,
            )
            return await finish(
                {
                    "id": record_id,
                    "passport_number": passport_number,
                    "first_applyid": first_applyid,
                    "ok": False,
                    "reason": "api need new token",
                },
                None,
            )

        remote_status = _extract_remote_status(matched_row) or str(
            row.get("status") or "draft"
        )
        internal_status = _map_apply_status_to_internal(remote_status)
        application_code = _extract_remote_application_code(matched_row)
        existing_payload = (
            row.get("payload") if isinstance(row.get("payload"), dict) else {}
        )
        update = {
            "record_id": record_id,
            "status": internal_status,
            "application_code": application_code,
            "payload": {
                **existing_payload,
                "sync": {
                    "first_applyid": first_applyid,
                    "application_code": application_code,
                    "full_name": full_name,
                    "passport_number": passport_number,
                    "visa_type": visa_type,
                    "matched_row": matched_row,
                    "api_response": response,
                    "apply_status": remote_status,
                    "internal_status": internal_status,
                },
            },
        }
        item = {
            "id": record_id,
            "full_name": full_name,
            "passport_number": passport_number,
            "visa_type": visa_type,
            "first_applyid": first_applyid,
            "application_code": application_code,
            "ok": False,
            "remote_applyid": _extract_remote_applyid(matched_row),
            "remote_status": remote_status,
            "internal_status": internal_status,
        }
        return await finish(item, update)

    api_started_at = time.perf_counter()
    api_expected = sum(
        1
        for row in total_rows
        if _should_sync_row_with_api(row)
    )
    print(
        "[sync_draft] api calls start "
        f"api_expected={api_expected} display_only={len(total_rows) - api_expected} "
        f"total={len(total_rows)} concurrency={max(1, concurrency)}",
        flush=True,
    )
    async with httpx.AsyncClient(timeout=60) as client:
        results = await asyncio.gather(
            *(process_row(client, row) for row in total_rows)
        )
    print(
        f"[sync_draft] api calls done duration={time.perf_counter() - api_started_at:.2f}s",
        flush=True,
    )

    updates = [update for _, update in results if update is not None]
    update_started_at = time.perf_counter()
    print(f"[sync_draft] db update start count={len(updates)}", flush=True)
    updated_count = batch_update_visa_registration_status_and_payload(updates)
    print(
        "[sync_draft] db update done "
        f"updated={updated_count}/{len(updates)} "
        f"duration={time.perf_counter() - update_started_at:.2f}s",
        flush=True,
    )
    summary["updated"] = updated_count

    cleanup_started_at = time.perf_counter()
    approved_cleanup_count = 0
    successful_update_slots = updated_count
    for item, update in results:
        if update is None:
            if item.get("reason") == "display_only_no_api_sync":
                summary["display_only"] += 1
            else:
                summary["skipped"] += 1
            summary["items"].append(item)
            continue

        item["ok"] = successful_update_slots > 0
        if successful_update_slots > 0:
            successful_update_slots -= 1
        summary["matched"] += 1

        if item.get("internal_status") == "approved":
            passport_number = str(item.get("passport_number") or "").strip()
            if passport_number:
                approved_cleanup_count += 1
                print(
                    f"[sync_draft] approved cleanup passport={passport_number}",
                    flush=True,
                )
                remove_r2.delete_r2_folder(passport_number)
                item["deleted_others"] = (
                    delete_visa_registrations_by_passport_except_status(
                        passport_number=passport_number,
                        status="approved",
                    )
                )
        summary["items"].append(item)
    if approved_cleanup_count:
        print(
            "[sync_draft] approved cleanup done "
            f"count={approved_cleanup_count} "
            f"duration={time.perf_counter() - cleanup_started_at:.2f}s",
            flush=True,
        )

    sheet_url = spreadsheet_url.strip() or os.getenv("GOOGLE_SHEET_SYNC_URL", "").strip()
    if sheet_url and not skip_google_sheet:
        try:
            sheet_started_at = time.perf_counter()
            print(
                f"[sync_draft] google sheet start worksheet={worksheet_name} mode={sheet_mode}",
                flush=True,
            )
            sheet_result = write_sync_summary_to_google_sheet(
                summary=summary,
                spreadsheet_url=sheet_url,
                worksheet_name=worksheet_name,
                mode=sheet_mode,
            )
            summary["google_sheet"] = sheet_result
            print(
                "[sync_draft] google sheet done "
                f"duration={time.perf_counter() - sheet_started_at:.2f}s "
                f"result_ok={sheet_result.get('ok')}",
                flush=True,
            )
        except Exception as exc:
            summary["google_sheet"] = {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }
            print(
                "[sync_draft] google sheet failed "
                f"error={type(exc).__name__} message={exc}",
                flush=True,
            )
    elif sheet_url and skip_google_sheet:
        print("[sync_draft] google sheet skipped by request", flush=True)
    else:
        print("[sync_draft] google sheet skipped no sheet_url", flush=True)

    print(
        "[sync_draft] done "
        f"total={summary['total']} matched={summary['matched']} "
        f"updated={summary['updated']} skipped={summary['skipped']} "
        f"display_only={summary['display_only']} "
        f"duration={time.perf_counter() - started_at:.2f}s",
        flush=True,
    )

    return summary
