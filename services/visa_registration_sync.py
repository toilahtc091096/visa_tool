from __future__ import annotations

import os
from typing import Any

import httpx

from api import api_get_online_application_list_by_passport
from database.crud import (
    list_visa_registrations_by_status,
    update_visa_registration_status_and_payload,
    get_visa_registration_by_passport,
)
from services.google_sheets import write_sync_summary_to_google_sheet
from utils import load_authorization, load_login_payload, remove_r2


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


async def sync_draft_visa_registrations(
    page_num: int = 1,
    page_size: int = 1000,
    authorization: str = "",
    spreadsheet_url: str = "",
    worksheet_name: str = "sync_draft_visa_status",
    sheet_mode: str = "upsert",
) -> dict[str, Any]:
    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    tmp_secret = login_payload.get("tmpSecret", "")
    auth = authorization.strip() or load_authorization().strip() or None

    draft_rows = list_visa_registrations_by_status("draft")
    under_review_rows = list_visa_registrations_by_status("under_review")
    pending_review_rows = list_visa_registrations_by_status("pending_review")
    submitted_rows = list_visa_registrations_by_status("submitted")
    approved_rows = list_visa_registrations_by_status("approved")
    rejected_rows = list_visa_registrations_by_status("rejected")
    cancelled_rows = list_visa_registrations_by_status("cancelled")
    summary: dict[str, Any] = {
        "ok": True,
        "draft_total": len(draft_rows),
        "matched": 0,
        "updated": 0,
        "skipped": 0,
        "items": [],
    }
    total_rows = draft_rows + under_review_rows + pending_review_rows + submitted_rows + approved_rows +rejected_rows + cancelled_rows

    async with httpx.AsyncClient(timeout=60) as client:
        for row in total_rows:
            record_id = row.get("id")
            first_applyid = str(row.get("first_applyid") or "").strip()
            passport_number = str(row.get("passport_number") or "").strip()
            visa_type = str(row.get("visa_type") or "").strip()

            if not passport_number:
                summary["skipped"] += 1
                summary["items"].append(
                    {
                        "id": record_id,
                        "passport_number": passport_number,
                        "ok": False,
                        "reason": "missing_passport_number",
                    }
                )
                continue

            if not first_applyid:
                summary["skipped"] += 1
                summary["items"].append(
                    {
                        "id": record_id,
                        "passport_number": passport_number,
                        "ok": False,
                        "reason": "missing_first_applyid",
                    }
                )
                continue

            ok, remote = await api_get_online_application_list_by_passport(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                passportNo=passport_number,
                pageNum=page_num,
                pageSize=page_size,
                authorization=auth,
            )

            if not ok:
                summary["skipped"] += 1
                summary["items"].append(
                    {
                        "id": record_id,
                        "passport_number": passport_number,
                        "ok": False,
                        "reason": "remote_api_failed",
                        "remote": remote,
                    }
                )
                continue

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
                summary["skipped"] += 1
                summary["items"].append(
                    {
                        "id": record_id,
                        "passport_number": passport_number,
                        "first_applyid": first_applyid,
                        "ok": False,
                        "reason": "api need new token",
                    }
                )
                continue

            remote_status = _extract_remote_status(matched_row) or str(
                row.get("status") or "draft"
            )
            internal_status = _map_apply_status_to_internal(remote_status)
            if internal_status == "approved": 
                remove_r2.delete_r2_folder(passport_number)     
            existing_payload = (
                row.get("payload") if isinstance(row.get("payload"), dict) else {}
            )
            info_by_passport_number = get_visa_registration_by_passport(passport_number)
            full_name = ""
            if info_by_passport_number is not None:
                full_name = info_by_passport_number.get("full_name")
            updated = update_visa_registration_status_and_payload(
                record_id=record_id,
                status=internal_status,
                payload={
                    **existing_payload,
                    "sync": {
                        "first_applyid": first_applyid,
                        "full_name": full_name,
                        "passport_number": passport_number,
                        "visa_type": visa_type,
                        "matched_row": matched_row,
                        "api_response": response,
                        "apply_status": remote_status,
                        "internal_status": internal_status,
                    },
                },
            )
            summary["matched"] += 1
            summary["updated"] += 1 if updated else 0
            summary["items"].append(
                {
                    "id": record_id,
                    "full_name": full_name,
                    "passport_number": passport_number,
                    "visa_type": visa_type,
                    "first_applyid": first_applyid,
                    "ok": updated,
                    "remote_applyid": _extract_remote_applyid(matched_row),
                    "remote_status": remote_status,
                    "internal_status": internal_status,
                }
            )
    sheet_url = (
        spreadsheet_url.strip() or os.getenv("GOOGLE_SHEET_SYNC_URL", "").strip()
    )
    if sheet_url:
        try:
            sheet_result = write_sync_summary_to_google_sheet(
                summary=summary,
                spreadsheet_url=sheet_url,
                worksheet_name=worksheet_name,
                mode=sheet_mode,
            )
            summary["google_sheet"] = sheet_result
        except Exception as exc:
            summary["google_sheet"] = {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }

    return summary