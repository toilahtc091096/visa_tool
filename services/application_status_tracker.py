"""Theo dõi trạng thái hồ sơ theo số hộ chiếu nhận từ nhóm Zalo.

Luồng:
    zalo-bridge (zca-js) -> POST /zalo/inbound -> ZaloInbox gom mã HC theo người gửi
    -> "xong" hoặc im lặng TRACKER_IDLE_SECONDS -> process_passport_batch
    -> lưu bảng application_status_trackings + Google Sheet -> trả lời nhóm.
    Scheduler -> check_tracked_applications -> hồ sơ đổi trạng thái thì cập nhật
    sheet và nhắn nhóm. Token hỏng -> nhắn riêng TRACKER_ADMIN_ZALO_ID (1 lần).
    Ai trong nhóm nhắn "token: <authorization>" -> lưu token mới và check lại ngay.
"""

from __future__ import annotations

import asyncio
import os
import re
import threading
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

import gspread
import httpx

from api.get_list_old_by_visa_number import api_list_online_applications
from api.token_check import check_token_alive, describe_token_error
from database.crud import (
    create_tracking,
    get_active_tracking_by_passport,
    get_visa_registration_by_passport,
    list_active_trackings,
    list_finished_tracking_applyids,
    update_tracking,
)
from services.google_sheets import (
    _chunked,
    _column_number_to_letter,
    _load_service_account_client,
    extract_spreadsheet_id,
)
from services.visa_registration_sync import (
    TERMINAL_STATUSES,
    _extract_remote_application_code,
    _extract_remote_applyid,
    _extract_remote_passport,
    _extract_remote_rows,
    _extract_remote_status,
    _map_apply_status_to_internal,
)
from services.zalo_notify import notify_admin, notify_group
from utils.token_store import append_authorization, load_authorization, load_login_payload


DEFAULT_PASSPORT_PATTERN = r"\b[A-Z]{1,2}\d{7,8}\b"
DEFAULT_DONE_KEYWORDS = "xong,done,/done,het,hết"
TOKEN_MESSAGE_RE = re.compile(r"^\s*token\s*[:：=]\s*(.+?)\s*$", re.IGNORECASE | re.DOTALL)

STATUS_NOT_CHECKED = "not_checked"
STATUS_NOT_FOUND = "not_found"
STATUS_LABELS = {
    "under_review": "Under review",
    "pending_review": "Pending review",
    "submitted": "Submitted",
    "draft": "Draft",
    "approved": "Approved",
    "rejected": "Rejected",
    "cancelled": "Cancelled",
    "unknown": "Không rõ",
    STATUS_NOT_FOUND: "Chưa thấy trên hệ thống",
    STATUS_NOT_CHECKED: "Chưa check",
}

SHEET_HEADERS = [
    "STT",
    "ID",
    "Số HC",
    "Họ tên",
    "Mã đơn",
    "applyid",
    "Trạng thái ban đầu",
    "Trạng thái hiện tại",
    "Trạng thái gốc",
    "Ngày đưa vào",
    "Ngày đổi trạng thái",
    "Check gần nhất",
    "Đang theo dõi",
    "Người gửi",
    "Ghi chú",
]
_SHEET_ID_COLUMN_INDEX = 1

_SHEET_LOCK = threading.Lock()
_TOKEN_ALERT_LOCK = threading.Lock()
_token_alert_state: dict[str, Any] = {"sent": False}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_list(name: str, default: str = "") -> list[str]:
    raw_value = _env(name, default)
    return [item.strip() for item in raw_value.replace(";", ",").split(",") if item.strip()]


def _local_timezone() -> tzinfo:
    try:
        return ZoneInfo(_env("APP_TIMEZONE", "Asia/Bangkok"))
    except Exception:
        return timezone(timedelta(hours=7))


def _now() -> datetime:
    return datetime.now(_local_timezone())


def _format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(_local_timezone()).strftime("%d/%m/%Y %H:%M")
    return str(value or "")


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status or "")


def parse_passport_numbers(text: str) -> list[str]:
    """Lấy các số HC trong tin nhắn; câu không có mã HC trả về list rỗng."""
    pattern = re.compile(_env("TRACKER_PASSPORT_REGEX", DEFAULT_PASSPORT_PATTERN))
    return list(dict.fromkeys(pattern.findall(str(text or "").upper())))


def parse_token_message(text: str) -> str:
    match = TOKEN_MESSAGE_RE.match(str(text or ""))
    return match.group(1).strip() if match else ""


def is_done_message(text: str) -> bool:
    keywords = {item.casefold() for item in _env_list("TRACKER_DONE_KEYWORDS", DEFAULT_DONE_KEYWORDS)}
    words = re.findall(r"[^\s,;.!?]+", str(text or "").casefold())
    return bool(words) and (words[0] in keywords or words[-1] in keywords)


# ---------------------------------------------------------------------------
# Google Sheet
# ---------------------------------------------------------------------------


def _open_tracker_worksheet() -> gspread.Worksheet | None:
    spreadsheet_url = _env("TRACKER_SHEET_URL") or _env("GOOGLE_SHEET_SYNC_URL")
    if not spreadsheet_url:
        return None

    worksheet_name = _env("TRACKER_WORKSHEET", "theo_doi_HC")
    spreadsheet = _load_service_account_client().open_by_key(
        extract_spreadsheet_id(spreadsheet_url)
    )
    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name, rows=1000, cols=len(SHEET_HEADERS)
        )
        worksheet.update("A1", [SHEET_HEADERS], value_input_option="RAW")
        return worksheet


def _build_sheet_row(tracking: dict[str, Any], stt: Any) -> list[Any]:
    return [
        stt,
        str(tracking.get("id") or ""),
        tracking.get("passport_number") or "",
        tracking.get("full_name") or "",
        tracking.get("application_code") or "",
        tracking.get("first_applyid") or "",
        status_label(tracking.get("initial_status") or ""),
        status_label(tracking.get("current_status") or ""),
        tracking.get("apply_status_raw") or "",
        _format_datetime(tracking.get("added_at")),
        _format_datetime(tracking.get("status_changed_at")),
        _format_datetime(tracking.get("last_checked_at")),
        "Có" if tracking.get("is_active") else "Không",
        tracking.get("sender_name") or tracking.get("sender_id") or "",
        tracking.get("note") or "",
    ]


def sync_trackings_to_sheet(trackings: list[dict[str, Any]]) -> dict[str, Any]:
    """Upsert các dòng theo cột ID (= id trong bảng application_status_trackings)."""
    if not trackings:
        return {"ok": True, "updated": 0, "appended": 0}

    try:
        with _SHEET_LOCK:
            worksheet = _open_tracker_worksheet()
            if worksheet is None:
                return {"ok": False, "error": "missing TRACKER_SHEET_URL"}

            values = worksheet.get_all_values()
            if not values:
                worksheet.update("A1", [SHEET_HEADERS], value_input_option="RAW")
                values = [SHEET_HEADERS]

            row_by_id: dict[str, tuple[int, str]] = {}
            for row_num, row in enumerate(values[1:], start=2):
                if len(row) > _SHEET_ID_COLUMN_INDEX and row[_SHEET_ID_COLUMN_INDEX].strip():
                    row_by_id[row[_SHEET_ID_COLUMN_INDEX].strip()] = (row_num, row[0])

            last_column = _column_number_to_letter(len(SHEET_HEADERS))
            next_stt = sum(1 for row in values[1:] if any(cell.strip() for cell in row)) + 1
            batch_updates: list[dict[str, Any]] = []
            rows_to_append: list[list[Any]] = []
            for tracking in trackings:
                key = str(tracking.get("id") or "")
                if key in row_by_id:
                    row_num, stt = row_by_id[key]
                    batch_updates.append(
                        {
                            "range": f"A{row_num}:{last_column}{row_num}",
                            "values": [_build_sheet_row(tracking, stt)],
                        }
                    )
                else:
                    rows_to_append.append(_build_sheet_row(tracking, next_stt))
                    next_stt += 1

            for chunk in _chunked(batch_updates, 100):
                worksheet.batch_update(chunk, value_input_option="RAW")
            if rows_to_append:
                worksheet.append_rows(rows_to_append, value_input_option="RAW")

        return {"ok": True, "updated": len(batch_updates), "appended": len(rows_to_append)}
    except Exception as exc:
        print(f"[tracker] google sheet failed {type(exc).__name__}: {exc}", flush=True)
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# token
# ---------------------------------------------------------------------------


def _reset_token_alert() -> None:
    with _TOKEN_ALERT_LOCK:
        _token_alert_state["sent"] = False


async def _alert_token_expired(reason: str) -> None:
    with _TOKEN_ALERT_LOCK:
        if _token_alert_state["sent"]:
            return
        _token_alert_state["sent"] = True

    text = (
        "⚠️ Token tra cứu hồ sơ không dùng được, cần cập nhật.\n"
        f"Lúc: {_format_datetime(_now())}\n"
        f"Lý do: {reason}\n"
        "Nhắn vào nhóm theo dạng: token: <authorization>"
    )
    print(f"[tracker] token expired reason={reason}", flush=True)
    if _env("TRACKER_ADMIN_ZALO_ID"):
        await notify_admin(text)
    else:
        await notify_group(text)


# ---------------------------------------------------------------------------
# kiểm tra trạng thái
# ---------------------------------------------------------------------------


def _remote_row_time(row: dict[str, Any]) -> str:
    for key in ("updateTimeLocal", "updateTime", "createTimeLocal", "createTime"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _resolve_first_applyid(tracking: dict[str, Any], finished_applyids: set[str]) -> str:
    """first_applyid lấy từ bảng visa_registrations; bỏ qua hồ sơ của lượt đi trước."""
    if tracking.get("first_applyid"):
        return str(tracking["first_applyid"])

    registration = get_visa_registration_by_passport(tracking["passport_number"])
    applyid = str((registration or {}).get("first_applyid") or "").strip()
    return "" if applyid in finished_applyids else applyid


def _pick_remote_row(
    rows: list[dict[str, Any]],
    passport_number: str,
    first_applyid: str,
    finished_applyids: set[str],
) -> dict[str, Any] | None:
    same_passport = [
        row
        for row in rows
        if _extract_remote_passport(row).upper() in ("", passport_number)
    ]
    if first_applyid:
        for row in same_passport:
            if _extract_remote_applyid(row) == first_applyid:
                return row
        return None

    # Không có trong DB -> lấy hồ sơ mới nhất chưa thuộc lượt đã xong.
    candidates = [
        row for row in same_passport if _extract_remote_applyid(row) not in finished_applyids
    ]
    candidates.sort(key=_remote_row_time, reverse=True)
    return candidates[0] if candidates else None


async def _check_one(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    tracking: dict[str, Any],
    token: str,
    tmp_secret: str,
    authorization: str,
) -> dict[str, Any]:
    passport_number = tracking["passport_number"]
    async with semaphore:
        ok, remote = await api_list_online_applications(
            client=client,
            token=token,
            tmp_secret=tmp_secret,
            passportNo=passport_number,
            pageNum=1,
            pageSize=50,
            authorization=authorization or None,
        )

    if not ok:
        return {"tracking": tracking, "error": f"http_{remote.get('status_code')} {remote.get('error', '')}"}

    response = remote.get("response") or {}
    token_error = describe_token_error(response)
    if token_error:
        return {"tracking": tracking, "token_error": token_error}

    finished_applyids = list_finished_tracking_applyids(passport_number)
    first_applyid = _resolve_first_applyid(tracking, finished_applyids)
    matched_row = _pick_remote_row(
        _extract_remote_rows(response), passport_number, first_applyid, finished_applyids
    )

    checked_at = _now()
    old_status = str(tracking.get("current_status") or STATUS_NOT_CHECKED)
    fields: dict[str, Any] = {"last_checked_at": checked_at}
    remote_time = ""
    if matched_row is None:
        new_status = STATUS_NOT_FOUND
        fields["apply_status_raw"] = ""
        fields["note"] = (
            f"Chưa thấy applyid {first_applyid} trên hệ thống"
            if first_applyid
            else "Chưa thấy hồ sơ trên hệ thống"
        )
    else:
        raw_status = _extract_remote_status(matched_row)
        new_status = _map_apply_status_to_internal(raw_status)
        remote_time = _remote_row_time(matched_row)
        fields.update(
            {
                "apply_status_raw": raw_status,
                "first_applyid": _extract_remote_applyid(matched_row),
                "application_code": _extract_remote_application_code(matched_row),
                "note": "",
            }
        )

    if not tracking.get("full_name"):
        registration = get_visa_registration_by_passport(passport_number)
        if registration and registration.get("full_name"):
            fields["full_name"] = str(registration["full_name"]).strip()

    fields["current_status"] = new_status
    fields["is_active"] = new_status not in TERMINAL_STATUSES
    if not tracking.get("initial_status"):
        fields["initial_status"] = new_status

    change = None
    if new_status != old_status:
        fields["status_changed_at"] = checked_at
        payload = dict(tracking.get("payload") or {})
        history = list(payload.get("history") or [])
        history.append(
            {
                "from": old_status,
                "to": new_status,
                "apply_status_raw": fields.get("apply_status_raw", ""),
                "remote_time": remote_time,
                "checked_at": checked_at.isoformat(),
            }
        )
        payload["history"] = history
        fields["payload"] = payload
        if old_status != STATUS_NOT_CHECKED:
            change = {
                "from": old_status,
                "to": new_status,
                "remote_time": remote_time,
                "checked_at": checked_at,
            }

    updated = await asyncio.to_thread(update_tracking, tracking["id"], fields)
    return {"tracking": updated or {**tracking, **fields}, "change": change}


async def _check_trackings(trackings: list[dict[str, Any]]) -> dict[str, Any]:
    if not trackings:
        return {"ok": True, "results": []}

    async with httpx.AsyncClient(timeout=60) as client:
        token_state = await check_token_alive(client)
        if not token_state["ok"]:
            await _alert_token_expired(token_state["reason"])
            return {"ok": False, "token_expired": True, "reason": token_state["reason"], "results": []}
        _reset_token_alert()

        payload = load_login_payload()
        semaphore = asyncio.Semaphore(max(1, int(_env("TRACKER_CONCURRENCY", "5") or 5)))
        results = await asyncio.gather(
            *(
                _check_one(
                    client,
                    semaphore,
                    tracking,
                    str(payload.get("token", "") or ""),
                    str(payload.get("tmpSecret", "") or ""),
                    load_authorization(),
                )
                for tracking in trackings
            )
        )

    token_errors = [result["token_error"] for result in results if result.get("token_error")]
    if token_errors:
        await _alert_token_expired(token_errors[0])
    return {"ok": not token_errors, "token_expired": bool(token_errors), "results": results}


def _format_change_message(tracking: dict[str, Any], change: dict[str, Any]) -> str:
    name = f" ({tracking['full_name']})" if tracking.get("full_name") else ""
    lines = [
        f"🔔 HC {tracking['passport_number']}{name}",
        f"Trạng thái: {status_label(change['from'])} → {status_label(change['to'])}",
    ]
    if change.get("remote_time"):
        lines.append(f"Thay đổi lúc: {change['remote_time']} (theo hệ thống)")
    lines.append(f"Check lúc: {_format_datetime(change['checked_at'])}")
    return "\n".join(lines)


async def check_tracked_applications() -> dict[str, Any]:
    """Check lại toàn bộ hồ sơ đang theo dõi; hồ sơ đổi trạng thái thì nhắn nhóm."""
    trackings = await asyncio.to_thread(list_active_trackings)
    print(f"[tracker] check start active={len(trackings)}", flush=True)
    result = await _check_trackings(trackings)
    results = result["results"]

    updated_rows = [item["tracking"] for item in results if "change" in item]
    sheet_result = await asyncio.to_thread(sync_trackings_to_sheet, updated_rows)

    messages_by_group: dict[str, list[str]] = {}
    for item in results:
        if item.get("change"):
            tracking = item["tracking"]
            messages_by_group.setdefault(str(tracking.get("group_id") or ""), []).append(
                _format_change_message(tracking, item["change"])
            )
    for group_id, messages in messages_by_group.items():
        await notify_group("\n\n".join(messages), group_id)

    summary = {
        "ok": result["ok"],
        "token_expired": result.get("token_expired", False),
        "active": len(trackings),
        "checked": len(updated_rows),
        "changed": sum(len(messages) for messages in messages_by_group.values()),
        "errors": [
            {"passport_number": item["tracking"].get("passport_number"), "error": item["error"]}
            for item in results
            if item.get("error")
        ],
        "google_sheet": sheet_result,
    }
    print(
        "[tracker] check done "
        f"active={summary['active']} checked={summary['checked']} "
        f"changed={summary['changed']} token_expired={summary['token_expired']}",
        flush=True,
    )
    return summary


# ---------------------------------------------------------------------------
# xử lý tin nhắn
# ---------------------------------------------------------------------------


async def process_passport_batch(
    passport_numbers: list[str],
    group_id: str = "",
    sender_id: str = "",
    sender_name: str = "",
) -> dict[str, Any]:
    """Bước 1 + 2: thêm HC mới vào theo dõi, bỏ qua HC đang theo dõi."""
    added: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for passport_number in passport_numbers:
        active = await asyncio.to_thread(get_active_tracking_by_passport, passport_number)
        if active is None:
            created = await asyncio.to_thread(
                create_tracking, passport_number, group_id, sender_id, sender_name
            )
            if created is not None:
                added.append(created)
                continue
            # Vừa có batch khác tạo trước (unique index) -> coi như đang theo dõi.
            active = await asyncio.to_thread(get_active_tracking_by_passport, passport_number)
        skipped.append(active or {"passport_number": passport_number})

    check_result = await _check_trackings(added)
    checked_by_id = {item["tracking"]["id"]: item for item in check_result["results"]}
    added_rows = [checked_by_id.get(row["id"], {}).get("tracking") or row for row in added]
    sheet_result = await asyncio.to_thread(sync_trackings_to_sheet, added_rows)

    lines = [f"✅ Đã nhận {len(passport_numbers)} HC lúc {_format_datetime(_now())}"]
    if added_rows:
        lines.append(f"➕ Thêm mới ({len(added_rows)}):")
        lines.extend(
            f"  • {row['passport_number']} – {status_label(row.get('current_status') or '')}"
            for row in added_rows
        )
    if skipped:
        lines.append(f"⏭ Bỏ qua – đang theo dõi ({len(skipped)}):")
        lines.extend(
            f"  • {row['passport_number']} – {status_label(row.get('current_status') or '')}"
            for row in skipped
        )
    if check_result.get("token_expired"):
        lines.append("⚠️ Token hết hạn, sẽ check trạng thái khi có token mới.")
    if not sheet_result.get("ok"):
        lines.append(f"⚠️ Ghi Google Sheet lỗi: {sheet_result.get('error')}")
    await notify_group("\n".join(lines), group_id)

    return {
        "ok": True,
        "added": [row["passport_number"] for row in added_rows],
        "skipped": [row["passport_number"] for row in skipped],
        "token_expired": check_result.get("token_expired", False),
        "google_sheet": sheet_result,
    }


async def update_authorization(
    authorization: str,
    group_id: str = "",
    sender_name: str = "",
    run_check: bool = True,
) -> dict[str, Any]:
    """Lưu token mới (nhận từ nhóm hoặc API) nếu login được, rồi check lại hồ sơ."""
    async with httpx.AsyncClient(timeout=60) as client:
        token_state = await check_token_alive(client, authorization=authorization, force_relogin=True)

    if not token_state["ok"]:
        if group_id:
            await notify_group(
                f"❌ Token vừa gửi{f' ({sender_name})' if sender_name else ''} "
                f"không dùng được: {token_state['reason']}",
                group_id,
            )
        return {"ok": False, "reason": token_state["reason"]}

    append_authorization(authorization)
    _reset_token_alert()
    if group_id:
        await notify_group(
            f"✅ Đã cập nhật token{f' từ {sender_name}' if sender_name else ''}, token hoạt động.",
            group_id,
        )

    check_summary = await check_tracked_applications() if run_check else None
    return {"ok": True, "check": check_summary}


def _run_in_thread(coro_factory, *args, **kwargs):
    """DB/Google Sheet là blocking -> chạy trong thread với event loop riêng."""
    return asyncio.to_thread(asyncio.run, coro_factory(*args, **kwargs))


class ZaloInbox:
    """Gom mã HC theo (nhóm, người gửi) cho tới khi họ nhắn "xong" hoặc im lặng."""

    def __init__(self) -> None:
        self._buffers: dict[tuple[str, str], dict[str, Any]] = {}
        self._tasks: set[asyncio.Task] = set()

    def _spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_batch(self, key: tuple[str, str]) -> None:
        buffer = self._buffers.pop(key, None)
        if not buffer or not buffer["passports"]:
            return
        timer = buffer.get("timer")
        if timer is not None and timer is not asyncio.current_task():
            timer.cancel()
        try:
            result = await _run_in_thread(
                process_passport_batch,
                list(buffer["passports"]),
                key[0],
                key[1],
                buffer["sender_name"],
            )
            print(f"[tracker] batch done {result}", flush=True)
        except Exception as exc:
            print(f"[tracker] batch failed {type(exc).__name__}: {exc}", flush=True)

    async def _flush_after_idle(self, key: tuple[str, str], idle_seconds: int) -> None:
        await asyncio.sleep(idle_seconds)
        await self._run_batch(key)

    async def _update_token(self, authorization: str, group_id: str, sender_name: str) -> None:
        try:
            await _run_in_thread(update_authorization, authorization, group_id, sender_name)
        except Exception as exc:
            print(f"[tracker] token update failed {type(exc).__name__}: {exc}", flush=True)

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:
        group_id = str(message.get("thread_id") or "").strip()
        sender_id = str(message.get("sender_id") or "").strip()
        sender_name = str(message.get("sender_name") or "").strip()
        text = str(message.get("text") or "")

        allowed_groups = _env_list("TRACKER_ZALO_GROUP_ID")
        if allowed_groups and group_id not in allowed_groups:
            return {"action": "ignored", "reason": "other_group"}

        # Ai trong nhóm cũng được gửi token.
        authorization = parse_token_message(text)
        if authorization:
            self._spawn(self._update_token(authorization, group_id, sender_name))
            return {"action": "token"}

        allowed_senders = _env_list("TRACKER_ZALO_SENDER_IDS")
        if allowed_senders and sender_id not in allowed_senders:
            return {"action": "ignored", "reason": "sender_not_allowed"}

        key = (group_id, sender_id)
        passports = parse_passport_numbers(text)
        done = is_done_message(text)
        if not passports and not (done and key in self._buffers):
            return {"action": "ignored", "reason": "no_passport"}

        if passports:
            buffer = self._buffers.setdefault(
                key, {"passports": {}, "sender_name": sender_name, "timer": None}
            )
            buffer["passports"].update(dict.fromkeys(passports))
            if buffer["timer"] is not None:
                buffer["timer"].cancel()
            buffer["timer"] = None

        if done:
            self._spawn(self._run_batch(key))
            return {"action": "flush", "passports": passports}

        idle_seconds = max(10, int(_env("TRACKER_IDLE_SECONDS", "90") or 90))
        timer = asyncio.create_task(self._flush_after_idle(key, idle_seconds))
        self._buffers[key]["timer"] = timer
        return {
            "action": "buffered",
            "passports": passports,
            "pending": list(self._buffers[key]["passports"]),
        }
