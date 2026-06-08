from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import httpx

from api import api_get_online_application_list_by_passport
from database.crud import (
    list_visa_registrations_by_status,
    update_visa_registration_status_and_payload,
)
from utils import load_login_payload


def _parse_remote_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        try:
            millis = int(text)
            if len(text) >= 13:
                return datetime.fromtimestamp(millis / 1000).date()
            return datetime.fromtimestamp(millis).date()
        except Exception:
            return None

    candidates = [text[:10], text.replace("Z", "+00:00")]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate).date()
        except Exception:
            continue

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None


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


async def sync_draft_visa_registrations(
    page_num: int = 1,
    page_size: int = 10,
    authorization: str = "",
) -> dict[str, Any]:
    login_payload = load_login_payload()
    token = login_payload.get("token", "")
    tmp_secret = login_payload.get("tmpSecret", "")
    auth = authorization.strip() or os.getenv("ONLINE_LIST_AUTHORIZATION", "").strip()

    draft_rows = list_visa_registrations_by_status("draft")
    summary: dict[str, Any] = {
        "ok": True,
        "draft_total": len(draft_rows),
        "matched": 0,
        "updated": 0,
        "skipped": 0,
        "items": [],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        for row in draft_rows:
            record_id = row.get("id")
            passport_number = str(row.get("passport_number") or "").strip()
            local_created_at = row.get("created_at")
            local_date = (
                local_created_at.date()
                if hasattr(local_created_at, "date")
                else None
            )

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

            ok, remote = await api_get_online_application_list_by_passport(
                client=client,
                token=token,
                tmp_secret=tmp_secret,
                passportNo=passport_number,
                pageNum=page_num,
                pageSize=page_size,
                authorization=auth or None,
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

                remote_date = _parse_remote_date(
                    remote_row.get("createTime")
                    or remote_row.get("createTimeLocal")
                    or remote_row.get("submitTime")
                    or remote_row.get("submitTimeLocal")
                )
                if (
                    local_date is not None
                    and remote_date is not None
                    and remote_date == local_date
                ):
                    matched_row = remote_row
                    break

            if matched_row is None:
                summary["skipped"] += 1
                summary["items"].append(
                    {
                        "id": record_id,
                        "passport_number": passport_number,
                        "ok": False,
                        "reason": "no_matching_row",
                    }
                )
                continue

            remote_status = _extract_remote_status(matched_row) or str(
                row.get("status") or "draft"
            )
            internal_status = _map_apply_status_to_internal(remote_status)
            existing_payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            updated = update_visa_registration_status_and_payload(
                record_id=record_id,
                status=internal_status,
                payload={
                    **existing_payload,
                    "sync": {
                        "passport_number": passport_number,
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
                    "passport_number": passport_number,
                    "ok": updated,
                    "local_created_at": local_created_at.isoformat()
                    if hasattr(local_created_at, "isoformat")
                    else str(local_created_at),
                    "remote_createTime": matched_row.get("createTime"),
                    "remote_status": remote_status,
                    "internal_status": internal_status,
                }
            )

    return summary
