import asyncio
import json
import os
import threading
import time
import traceback
from contextlib import asynccontextmanager
from datetime import date
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Body, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor

from api import api_convert_input_pdfs
from api.convert_input_pdfs import api_cleanup_pdf_page_images, render_pdf_pages_to_r2
from api import api_download_r2_folder_zip
from api import api_download_r2_object_bytes
from api import api_delete_r2_objects
from api import api_archive_r2_folder, api_restore_r2_folder, api_stat_r2_folder
from api import api_find_case_images
from api import api_sign_and_push_image_to_r2
from constants import REGION, REGION_SOUTH
from database.connection import init_database
from database.crud import set_visa_registration_owner, set_visa_registration_vip
from main import build_case, main
from services.han_approval import (
    list_han_approval_jobs,
    process_han_approval_inbox,
    reset_han_approval_printed_status,
    retry_han_approval_jobs,
)
from services import sync_draft_visa_registrations
from services.agency import assign_agency_to_registration, reassign_agency
from services.agency_merge import is_agency_merge_enabled, merge_small_agencies
from services.agency_sheets import (
    remove_record_from_agency_sheet,
    write_agency_sheet_for_record,
)
from services.google_sheets import debug_google_sheet_access
from utils import convert_html_to_pdf, log_exception, upload_pdf_to_r2
from utils.app_logging import log_event
from utils.access_guard import GuardConfig, decide
from database.crud.web_user import authenticate_web_user, get_web_user_by_api_key
from services.web_portal import FormError as WebFormError
from services.web_portal import build_start_payload, start_case
from services.web_portal import history_entry as web_history_entry
from database.crud import web_curl
from services.web_portal import form_options as web_form_options
from services.web_portal import rerun_prepare as web_rerun_prepare
from services.web_portal import folder_stat as web_folder_stat_call
from services.web_portal import make_step as web_make_step
from services.web_portal import step_status as web_step_status
from services.web_portal import upload_file as web_upload_file
from services.web_portal import house_by_port as web_house_by_port
from services.web_portal import run_case as web_run_case
from services import web_portal
from services import bio_token
from database.crud.web_job import add_web_job_step, create_web_job, get_job_staff, get_web_job
from database.crud.web_job import now_iso as web_now_iso
from database.crud import admin_report
from database.house import HOUSES as HOUSE_NAMES
from utils.token_store import append_authorization, load_authorization

print("START", flush=True)


def _is_debug_enabled() -> bool:
    value = os.getenv("DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_sync_scheduler_enabled() -> bool:
    value = os.getenv("SYNC_DRAFT_SCHEDULER_ENABLED", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_sync_draft_enabled() -> bool:
    value = os.getenv("SYNC_DRAFT_ENABLED", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _sync_scheduler_interval_seconds() -> int:
    raw_value = os.getenv("SYNC_DRAFT_SCHEDULER_INTERVAL_SECONDS", "").strip()
    if not raw_value:
        return 12 * 60 * 60
    try:
        return max(60, int(raw_value))
    except ValueError:
        return 12 * 60 * 60


def _server_port() -> int:
    raw_value = os.getenv("PORT", "10000").strip()
    try:
        return int(raw_value)
    except ValueError:
        return 10000


def _scheduled_sync_kwargs() -> dict[str, str]:
    """Sheet settings shared by the scheduler and the sync after /run."""
    return {
        "spreadsheet_url": os.getenv("GOOGLE_SHEET_SYNC_URL", "").strip(),
        "worksheet_name": os.getenv("GOOGLE_SHEET_SYNC_WORKSHEET", "hai").strip(),
        "sheet_mode": os.getenv("GOOGLE_SHEET_SYNC_MODE", "upsert").strip(),
    }


async def _sync_draft_scheduler_loop() -> None:
    if not _is_sync_draft_enabled():
        print("[sync_draft_scheduler] disabled by SYNC_DRAFT_ENABLED=0", flush=True)
        return

    interval_seconds = _sync_scheduler_interval_seconds()

    while True:
        try:
            # DB, xóa R2, Google Sheet bên trong đều là blocking -> chạy ở thread
            # riêng với event loop riêng để không làm đứng các request khác.
            result = await asyncio.to_thread(
                asyncio.run,
                sync_draft_visa_registrations(**_scheduled_sync_kwargs()),
            )
            print(
                "[sync_draft_scheduler] completed "
                f"matched={result.get('matched', 0)} "
                f"updated={result.get('updated', 0)} "
                f"skipped={result.get('skipped', 0)} "
                f"display_only={result.get('display_only', 0)}",
                flush=True,
            )
        except asyncio.CancelledError:
            print("[sync_draft_scheduler] cancelled")
            raise
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[sync_draft_scheduler] failed: {type(exc).__name__}: {exc}")
            print(tb)
            log_exception(exc, {"path": "sync_draft_scheduler_loop"})

        await asyncio.sleep(interval_seconds)


AGENCY_MERGE_FIRST_DELAY_SECONDS = 10 * 60
AGENCY_MERGE_INTERVAL_SECONDS = 24 * 60 * 60


async def _agency_merge_loop() -> None:
    """South: once a day, small agencies with no new record for 2 weeks go to CHUNG."""
    await asyncio.sleep(AGENCY_MERGE_FIRST_DELAY_SECONDS)
    while True:
        try:
            result = await asyncio.to_thread(merge_small_agencies)
            print(f"[agency_merge] merged={[m['code'] for m in result.get('merged', [])]} ok={result.get('ok')}", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log_exception(exc, {"path": "agency_merge_loop"})
        await asyncio.sleep(AGENCY_MERGE_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    tasks = []
    if _is_sync_scheduler_enabled():
        tasks.append(asyncio.create_task(_sync_draft_scheduler_loop()))
    if is_agency_merge_enabled():
        tasks.append(asyncio.create_task(_agency_merge_loop()))
    yield
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def access_guard(request: Request, call_next):
    # See utils/access_guard.py. ACCESS_GUARD=off (default) | log | enforce.
    cfg = GuardConfig.from_env()
    if cfg.mode != "off":
        client_ip = request.client.host if request.client else ""
        decision = decide(cfg, request.url.path, client_ip, request.headers.get("x-api-key", ""))
        if not decision.allowed:
            log_event({
                "event": "access_guard",
                "mode": cfg.mode,
                "blocked": cfg.mode == "enforce",
                "reason": decision.reason,
                "path": request.url.path,
                "client": client_ip,
            })
            if cfg.mode == "enforce":
                return JSONResponse({"ok": False, "error": decision.reason}, status_code=decision.status)
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True}


# ---------- /web: input form replacing WF-01 node 2 (open in the access guard; own key check) ----------
_WEB_PAGE = Path(__file__).resolve().parent / "web" / "index.html"
_login_failures: dict[str, list[float]] = {}


def _web_user(request: Request) -> dict[str, Any]:
    user = get_web_user_by_api_key(request.headers.get("x-api-key", ""))
    if not user:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "Phiên đăng nhập không hợp lệ, hãy đăng nhập lại"})
    return user


@app.get("/web")
def web_page():
    return HTMLResponse(_WEB_PAGE.read_text(encoding="utf-8"))


@app.post("/web/login")
def web_login(request: Request, payload: dict[str, Any] = Body(...)):
    ip = request.client.host if request.client else ""
    now = time.time()
    recent = [t for t in _login_failures.get(ip, []) if now - t < 600]
    if len(recent) >= 5:
        raise HTTPException(status_code=429, detail={"ok": False, "error": "Sai quá 5 lần, thử lại sau 10 phút"})
    user = authenticate_web_user(str(payload.get("username", "")), str(payload.get("password", "")))
    if not user:
        _login_failures[ip] = recent + [now]
        raise HTTPException(status_code=401, detail={"ok": False, "error": "Sai tên đăng nhập hoặc mật khẩu"})
    _login_failures.pop(ip, None)
    return {"ok": True, "username": user["username"], "staff": user["staff_code"], "api_key": user["api_key"], **web_form_options()}


@app.get("/web/me")
def web_me(request: Request):
    user = _web_user(request)
    return {"ok": True, "username": user["username"], "staff": user["staff_code"], **web_form_options()}


@app.post("/web/start")
def web_start(request: Request, payload: dict[str, Any] = Body(...)):
    user = _web_user(request)
    try:
        case = build_start_payload(user["staff_code"], payload)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    create_web_job(case, user["username"], web_make_step("received", "", web_now_iso()))
    try:
        result = start_case(case)
    except Exception as exc:
        log_exception(exc, {"event": "web_start_failed", "user": user["username"]})
        add_web_job_step(case["job_id"], web_make_step("error", f"Không gọi được n8n: {exc}", web_now_iso()), "error")
        raise HTTPException(status_code=502, detail={"ok": False, "error": str(exc)})
    log_event({"event": "web_start", "user": user["username"], "job_id": case["job_id"], "house": case["house"],
               "visa_type": case["visa_type"], "source_prefix": case["source_prefix"]})
    return {**result, "house": case["house"], "visa_type": case["visa_type"], "source_prefix": case["source_prefix"]}


@app.post("/web/rerun")
def web_rerun(request: Request, payload: dict[str, Any] = Body(...)):
    user = _web_user(request)
    try:
        result = web_rerun_prepare(payload)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    log_event({"event": "web_rerun", "user": user["username"], "confirm": bool(payload.get("confirm")),
               "house": payload.get("house"), "prefix": payload.get("source_prefix"), "ok": result.get("ok")})
    return result


@app.post("/web/run")
def web_run(request: Request, payload: dict[str, Any] = Body(...)):
    # Paste a curl from Telegram on the page, edit the JSON, run it (Postman-like).
    user = _web_user(request)
    try:
        house = payload.get("house") or web_house_by_port(payload.get("port"))
        body = payload.get("body")
        # A curl without `staff` (built before WF-13 sent it) counts for the person running it.
        if isinstance(body, dict) and not str(body.get("staff", "") or "").strip():
            body = {**body, "staff": user["staff_code"]}
        started = time.time()
        result = web_run_case(house, body)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        log_exception(exc, {"event": "web_run_failed", "user": user["username"]})
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không gọi được /run: {exc}"})
    seconds = round(time.time() - started, 1)
    if result.get("ok") and isinstance(body, dict):
        # Successful runs go to the curl history (15 days) so the curl can be reused from the page.
        try:
            result["history_id"] = web_curl.save_curl(web_history_entry(user, result, payload.get("port"), body, seconds))
        except Exception as exc:
            log_exception(exc, {"event": "web_curl_save_failed", "user": user["username"]})
    body = payload.get("body") or {}
    log_event({"event": "web_run", "user": user["username"], "house": result["house"], "status": result["status_code"],
               "passport": body.get("passportNumber", ""), "seconds": seconds})
    return result


@app.get("/web/curl-history")
def web_curl_history(request: Request, q: str = "", mine: str = ""):
    # Own history; ADMIN sees everyone's unless mine=1.
    user = _web_user(request)
    who = None if user["staff_code"] == "ADMIN" and mine != "1" else user["username"]
    return {"ok": True, "keep_days": web_curl.KEEP_DAYS, "items": web_curl.list_curls(who, q)}


@app.post("/web/progress")
def web_progress(request: Request, payload: dict[str, Any] = Body(...)):
    # Called by n8n at each milestone, with the shared VISA_API_KEY (not a user key).
    expected = os.getenv("VISA_API_KEY", "").strip()
    if not expected or request.headers.get("x-api-key", "") != expected:
        raise HTTPException(status_code=401, detail={"ok": False, "error": "bad key"})
    job_id = str(payload.get("job_id", "") or "").strip()
    try:
        step = web_make_step(str(payload.get("step", "")), str(payload.get("message", "") or ""), web_now_iso())
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    curl = str(payload.get("curl", "") or "")[:300_000]  # WF-13 sends the curl with the "done" step
    staff = str(payload.get("staff", "") or "").strip().upper()
    if job_id and staff:
        # WF01-GENERAL sends staff/house with its first step: a run started from WF-01 (not /web)
        # gets a job row too, so /run can tell who made the record. Existing (web) jobs are kept.
        create_web_job({"job_id": job_id, "staff": staff,
                        "house": str(payload.get("house", "") or "").strip().upper(),
                        "visa_type": str(payload.get("visa_type", "") or "").strip(),
                        "source_prefix": str(payload.get("source_prefix", "") or "").strip()},
                       "", web_make_step("received", "", web_now_iso()))
    known = bool(job_id) and add_web_job_step(job_id, step, web_step_status(step["step"]), curl)
    return {"ok": True, "tracked": known}  # False = run not started from /web (or already finished)


@app.get("/web/job/{job_id}")
def web_job(request: Request, job_id: str):
    user = _web_user(request)
    job = get_web_job(job_id)
    if not job or (job["username"] != user["username"] and user["staff_code"] != "ADMIN"):
        raise HTTPException(status_code=404, detail={"ok": False, "error": "Không tìm thấy lần chạy này"})
    return {"ok": True, "job": job, "now": web_now_iso()}


# ---------- /web admin: records of all houses (staff_code ADMIN only) ----------
_ADMIN_FILTER_KEYS = ("date_from", "date_to", "staff", "house", "visa_code", "status", "q", "agency", "vip")


def _web_admin(request: Request) -> dict[str, Any]:
    user = _web_user(request)
    if user["staff_code"] != "ADMIN":
        raise HTTPException(status_code=403, detail={"ok": False, "error": "Chỉ tài khoản ADMIN được xem trang này"})
    return user


def _admin_filters(request: Request) -> dict[str, str]:
    filters = {key: request.query_params.get(key, "") for key in _ADMIN_FILTER_KEYS}
    for key in ("date_from", "date_to"):
        if filters[key]:
            try:
                filters[key] = date.fromisoformat(filters[key]).isoformat()
            except ValueError:
                raise HTTPException(status_code=400, detail={"ok": False, "error": f"Ngày không hợp lệ: {filters[key]}"})
    return filters


@app.get("/web/admin/options")
def web_admin_options(request: Request):
    _web_admin(request)
    return {"ok": True, "staff": admin_report.list_staff_codes(), "houses": list(HOUSE_NAMES),
            "statuses": ["draft", "under_review", "pending_review", "submitted", "approved", "rejected", "cancelled"],
            "unknown_staff": admin_report.UNKNOWN_STAFF,
            "agencies": admin_report.list_agencies(), "unknown_agency": admin_report.UNKNOWN_AGENCY}


@app.get("/web/admin/stats")
def web_admin_stats(request: Request):
    _web_admin(request)
    return {"ok": True, "rows": admin_report.count_by_staff_day(_admin_filters(request))}


@app.get("/web/admin/charts")
def web_admin_charts(request: Request):
    _web_admin(request)
    return {"ok": True, **admin_report.chart_summary(_admin_filters(request))}


_STATS_PAGE = Path(__file__).resolve().parent / "web" / "stats.html"


@app.get("/web/stats")
def web_stats_page():
    # Chart page for ADMIN; the data endpoints above check the key.
    return HTMLResponse(_STATS_PAGE.read_text(encoding="utf-8"))


@app.get("/web/admin/records")
def web_admin_records(request: Request, limit: int = Query(50), offset: int = Query(0)):
    _web_admin(request)
    return {"ok": True, **admin_report.list_records(_admin_filters(request), limit=limit, offset=offset)}


# ---------- bio token (Tampermonkey script fills the house account, sends the token back) ----------
def _is_local_request(request: Request) -> bool:
    return (request.client.host if request.client else "") in ("127.0.0.1", "::1")


@app.get("/bio/credentials")
def bio_credentials(request: Request):
    # The house account (this instance's .env). Only from the VPS itself (the 10000 instance).
    if not _is_local_request(request):
        raise HTTPException(status_code=403, detail={"ok": False, "error": "local only"})
    cfg = bio_token.login_config()
    missing = [k for k, env in (("login_url", "BIO_LOGIN_URL"), ("username", "BIO_USERNAME"),
                                ("password", "BIO_PASSWORD")) if not cfg[k]]
    if missing:
        names = {"login_url": "BIO_LOGIN_URL", "username": "BIO_USERNAME", "password": "BIO_PASSWORD"}
        raise HTTPException(status_code=400, detail={"ok": False, "error": "Thiếu biến trong .env của nhà: "
                                                     + ", ".join(names[k] for k in missing)})
    return {"ok": True, **cfg}


@app.post("/bio/authorization")
def bio_save_authorization(payload: dict[str, Any] = Body(...)):
    # Check a bio token and keep it for this house: /run uses it when the curl has none.
    token = bio_token.normalize_authorization(payload.get("authorization"))
    valid, message = bio_token.check_authorization(token)
    if not valid:
        raise HTTPException(status_code=400, detail={"ok": False, "error": message})
    append_authorization(token)
    log_event({"event": "bio_token_saved", "token_tail": token[-8:]})
    return {"ok": True, "message": message}


@app.get("/bio/authorization/current")
def bio_current_authorization(request: Request):
    # The token this house uses now. Only from the VPS itself (the 10000 instance asks).
    if not _is_local_request(request):
        raise HTTPException(status_code=403, detail={"ok": False, "error": "local only"})
    return {"ok": True, "authorization": load_authorization()}


@app.get("/bio/authorization/check")
def bio_check_saved_authorization():
    token = load_authorization()
    if not token:
        return {"ok": True, "valid": False, "message": "Chưa có token"}
    valid, message = bio_token.check_authorization(token)
    return {"ok": True, "valid": valid, "message": message}


@app.post("/web/bio/start")
def web_bio_start(request: Request, payload: dict[str, Any] = Body(...)):
    user = _web_user(request)
    try:
        house = web_portal.house_config(payload.get("house"))["house"]
        cred = web_portal.bio_credentials(house)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không hỏi được instance nhà: {exc}"})
    if not cred.get("ok"):
        raise HTTPException(status_code=400, detail={"ok": False, "error": cred.get("error") or "Thiếu tài khoản bio"})
    ticket = bio_token.new_ticket(user["username"], house, cred["login_url"])
    sep = "&" if "#" in cred["login_url"] else "#"
    log_event({"event": "bio_token_start", "user": user["username"], "house": house})
    return {"ok": True, "ticket": ticket, "house": house, "open_url": f"{cred['login_url']}{sep}visa_tool={ticket}"}


@app.get("/web/bio/ticket/{ticket}")
def web_bio_ticket(ticket: str):
    # Called by the userscript on the bio tab: the ticket (random, 15 min, one run) is the key.
    t = bio_token.get_ticket(ticket)
    if not t:
        raise HTTPException(status_code=404, detail={"ok": False, "error": "Phiên lấy token đã hết hạn hoặc không tồn tại"})
    try:
        cred = web_portal.bio_credentials(t["house"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không hỏi được instance nhà: {exc}"})
    if not cred.get("ok"):
        raise HTTPException(status_code=400, detail={"ok": False, "error": cred.get("error") or "Thiếu tài khoản bio"})
    bio_token.set_ticket_state(ticket, "waiting", "Tab bio đã mở, đã điền tài khoản; chờ xác minh và đăng nhập")
    return {"ok": True, "house": t["house"], "username": cred["username"], "password": cred["password"],
            "login_url": cred.get("login_url") or t.get("login_url", "")}


@app.post("/web/bio/ticket/{ticket}/token")
def web_bio_ticket_token(ticket: str, payload: dict[str, Any] = Body(...)):
    t = bio_token.get_ticket(ticket)
    if not t:
        raise HTTPException(status_code=404, detail={"ok": False, "error": "Phiên lấy token đã hết hạn hoặc không tồn tại"})
    try:
        result = web_portal.bio_save_authorization(t["house"], str(payload.get("authorization", "") or ""))
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không lưu được token: {exc}"})
    if not result.get("ok"):
        bio_token.set_ticket_state(ticket, "waiting", result.get("error") or "Token chưa dùng được")
        raise HTTPException(status_code=400, detail={"ok": False, "error": result.get("error") or "Token chưa dùng được"})
    bio_token.set_ticket_state(ticket, "done", f"Đã cập nhật token nhà {t['house']}")
    log_event({"event": "bio_token_done", "user": t["username"], "house": t["house"]})
    return {"ok": True, "house": t["house"]}


@app.get("/web/bio/ticket/{ticket}/status")
def web_bio_ticket_status(request: Request, ticket: str):
    user = _web_user(request)
    status = bio_token.ticket_status(ticket)
    if not status or (status["username"] != user["username"] and user["staff_code"] != "ADMIN"):
        raise HTTPException(status_code=404, detail={"ok": False, "error": "Không tìm thấy phiên lấy token"})
    return {"ok": True, **{k: status[k] for k in ("house", "state", "message")}}


@app.post("/web/bio/manual")
def web_bio_manual(request: Request, payload: dict[str, Any] = Body(...)):
    # Fallback: the person pastes the page address / curl / token after logging in.
    user = _web_user(request)
    token = bio_token.extract_token(payload.get("value"))
    if not token:
        raise HTTPException(status_code=400, detail={"ok": False, "error": "Không tìm thấy token trong nội dung đã dán"})
    try:
        house = web_portal.house_config(payload.get("house"))["house"]
        result = web_portal.bio_save_authorization(house, token)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không lưu được token: {exc}"})
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"ok": False, "error": result.get("error") or "Token không dùng được"})
    log_event({"event": "bio_token_manual", "user": user["username"], "house": house})
    return {"ok": True, "house": house}


@app.get("/web/bio/token")
def web_bio_token(request: Request, house: str = Query("")):
    # Current token of the house: copy button, and filling "authorization" in the curl tab.
    _web_user(request)
    try:
        result = web_portal.bio_current_authorization(house)
        name = web_portal.house_config(house)["house"]
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không hỏi được instance nhà: {exc}"})
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail={"ok": False, "error": result.get("error") or "Không đọc được token"})
    return {"ok": True, "house": name, "authorization": result.get("authorization", "")}


@app.get("/web/bio/check")
def web_bio_check(request: Request, house: str = Query("")):
    _web_user(request)
    try:
        return web_portal.bio_check_authorization(house)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không hỏi được instance nhà: {exc}"})


@app.get("/web/case-image")
def web_case_image(request: Request, house: str = Query(""), passport: str = Query(""),
                   kind: str = Query(""), download: bool = Query(False)):
    # Passport image / edited portrait of a case, from the house's bucket (curl tab, after Chạy).
    _web_user(request)
    try:
        status, content, content_type, name = web_portal.case_image(house, passport, kind)
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"Không đọc được R2: {exc}"})
    if status == 404:
        raise HTTPException(status_code=404, detail={"ok": False, "error": "Chưa có ảnh này trên R2"})
    if status >= 400:
        raise HTTPException(status_code=502, detail={"ok": False, "error": f"R2 trả HTTP {status}"})
    headers = {"Cache-Control": "no-store"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{name}"'
    return Response(content=content, media_type=content_type, headers=headers)


@app.get("/web/visa-token.user.js")
def web_userscript(request: Request):
    base = str(request.base_url).rstrip("/")
    return Response(bio_token.userscript(base), media_type="text/javascript; charset=utf-8",
                    headers={"Cache-Control": "no-cache"})


@app.post("/web/folder-stat")
def web_folder_stat(request: Request, payload: dict[str, Any] = Body(...)):
    _web_user(request)
    try:
        return web_folder_stat_call(payload.get("house"), payload.get("source_prefix"))
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})


@app.post("/web/upload")
async def web_upload(
    request: Request,
    house: str = Form(""),
    source_prefix: str = Form(""),
    relative_path: str = Form(""),
    file: UploadFile = File(...),
):
    _web_user(request)
    content = await file.read()
    try:
        result = await asyncio.to_thread(
            web_upload_file, house, source_prefix, relative_path, content, file.content_type or ""
        )
    except WebFormError as exc:
        raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)})
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result)
    return {"ok": True, "key": result.get("key"), "size": result.get("size")}


@app.get("/r2/case-images")
def r2_case_images(passport: str = Query("")):
    # Keys of the passport image / edited portrait in this house's bucket (asked by /web).
    result = api_find_case_images(passport)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/r2/folders/stat")
def r2_folders_stat(payload: dict[str, Any] = Body(...)):
    result = api_stat_r2_folder(str(payload.get("prefix", "") or ""))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/run")
def run(payload: dict[str, Any] = Body(...)):
    payload = _authorization_for_run(payload)
    case = build_case(payload)
    location_pinyin = _location_pinyin(case)
    result = main(
        case,
        first_applyid=case.get("first_applyid", ""),
        is_update_info=case.get("is_update_info", False),
        upload_config_keys=case.get("upload_config_keys", []),
        apply_visa_validity=case.get("apply_visa_validity"),
        inviterFamilyName=case.get("inviterFamilyName", ""),
        inviterGivenName=case.get("inviterGivenName", ""),
        inviterIdCard=case.get("inviterIdCard", ""),
        inviterPhone=case.get("inviterPhone", case.get("inviter_id_phone", "")),
        inviteCompanyPhone=case.get("inviteCompanyPhone", ""),
        inviteZipCode=case.get("inviteZipCode", ""),
        inviterProvincePinyin=location_pinyin[0],
        inviterCityPinyin=location_pinyin[1],
        inviterDistrictPinyin=location_pinyin[2],
        inviterAddress=case.get("inviterAddress", ""),
        inviterRelation=case.get("inviterRelation", case.get("inviterrelation", "")),
        inviterName=case.get("inviterName", case.get("inviter_name", "")),
        emergencyFamilyName=case.get("emergencyFamilyName", ""),
        emergencyGivenName=case.get("emergencyGivenName", ""),
        emergencyRelationship=case.get("emergencyRelationship", ""),
        emergencyPhone=case.get("emergencyPhone", ""),
    )
    if result.get("ok"):
        # Before the sheet write below, so the row already has is_vip.
        is_vip = _save_is_vip(result.get("record_id"), payload)
        _save_owner(result.get("record_id"), payload)
        if is_vip is not None:
            result["is_vip"] = is_vip
        agency = assign_agency_to_registration(result.get("record_id"), payload)
        if agency:
            result["agency_code"] = agency["agency_code"]
            # Agency Google Sheet in the background: the response does not wait.
            # The sync later fills in the visa status columns.
            threading.Thread(
                target=_write_agency_sheet_safely,
                args=(result.get("record_id"), result.get("first_applyid"), agency),
                daemon=True,
            ).start()
        # Visa status of the new record (and the others) in the background.
        _request_sync_after_run(result.get("record_id"))
    return JSONResponse(status_code=_run_status_code(result), content=result)


def _is_sync_after_run_enabled() -> bool:
    value = os.getenv("SYNC_DRAFT_AFTER_RUN", "1").strip().lower()
    return (
        REGION == REGION_SOUTH
        and _is_sync_draft_enabled()
        and value in {"1", "true", "yes", "on"}
    )


# One sync after /run at a time: runs that succeed while it is going only ask
# for one more pass after it (a sync covers every draft record anyway).
_SYNC_AFTER_RUN_LOCK = threading.Lock()
_sync_after_run_state = {"running": False, "pending": False}


def _request_sync_after_run(record_id: int | None) -> None:
    if not _is_sync_after_run_enabled():
        return
    with _SYNC_AFTER_RUN_LOCK:
        if _sync_after_run_state["running"]:
            _sync_after_run_state["pending"] = True
            log_event({"step": "sync_after_run", "record_id": record_id, "queued": True})
            return
        _sync_after_run_state["running"] = True
    threading.Thread(
        target=_sync_after_run_worker, args=(record_id,), daemon=True
    ).start()


def _sync_after_run_worker(record_id: int | None) -> None:
    while True:
        started_at = time.perf_counter()
        try:
            result = asyncio.run(sync_draft_visa_registrations(**_scheduled_sync_kwargs()))
            log_event(
                {
                    "step": "sync_after_run",
                    "record_id": record_id,
                    "ok": True,
                    "matched": result.get("matched", 0),
                    "updated": result.get("updated", 0),
                    "skipped": result.get("skipped", 0),
                    "duration": round(time.perf_counter() - started_at, 2),
                }
            )
        except Exception as exc:
            log_exception(exc, {"path": "sync_after_run", "record_id": record_id})
        with _SYNC_AFTER_RUN_LOCK:
            if not _sync_after_run_state["pending"]:
                _sync_after_run_state["running"] = False
                return
            _sync_after_run_state["pending"] = False
            record_id = None  # this pass covers the queued runs


def _parse_is_vip(value: Any) -> bool:
    return str(value if value is not None else "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _save_is_vip(record_id: int | None, payload: dict[str, Any]) -> int | None:
    """
    Store is_vip (0/1 from the curl) on the registration. Without the field
    the stored value is kept (a new record defaults to 0). Never raises.
    """
    if not record_id or "is_vip" not in payload:
        return None
    is_vip = _parse_is_vip(payload.get("is_vip"))
    try:
        set_visa_registration_vip(record_id, is_vip)
    except Exception as exc:
        log_event(
            {
                "step": "save_is_vip",
                "ok": False,
                "record_id": record_id,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return None
    return int(is_vip)


def _authorization_for_run(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Token for this /run. Empty -> the house's stored token (build_case/main load it).
    Same as stored -> as is. Different: kept and stored only when the bio site
    accepts it; an old token from an old curl never replaces the stored one.
    """
    authorization = bio_token.normalize_authorization(payload.get("authorization"))
    if not authorization:
        return payload
    stored = load_authorization()
    if authorization == stored:
        return payload
    if stored:
        valid, message = bio_token.check_authorization(authorization)
        if not valid:
            log_event({"step": "run_authorization", "used": "stored", "reason": message,
                       "curl_token_tail": authorization[-8:]})
            return {**payload, "authorization": stored}
    append_authorization(authorization)
    log_event({"step": "run_authorization", "used": "curl", "saved": True, "token_tail": authorization[-8:]})
    return {**payload, "authorization": authorization}


def _save_owner(record_id: int | None, payload: dict[str, Any]) -> None:
    """
    Store who started the record. WF-13 puts the n8n `job_id` in the curl; the
    staff of that job is known from /web/start or from WF01-GENERAL's first
    progress call. `staff` in the body (added by /web/run) is used when the
    job is unknown. The first run keeps the owner. Never raises.
    """
    if not record_id:
        return
    job_id = str(payload.get("job_id", "") or "").strip()
    try:
        staff = get_job_staff(job_id) or str(payload.get("staff", "") or "").strip()
        if staff:
            set_visa_registration_owner(record_id, staff, job_id)
    except Exception as exc:
        log_event({"step": "save_owner", "ok": False, "record_id": record_id,
                   "error": f"{type(exc).__name__}: {exc}"})


def _write_agency_sheet_safely(
    record_id: int | None,
    first_applyid: str | None,
    agency: dict[str, Any],
) -> None:
    try:
        previous = agency.get("previous_agency_code") or ""
        if previous and previous != agency.get("agency_code"):
            # Re-run with another agency (e.g. was CHUNG): drop the old tab's row.
            remove_record_from_agency_sheet(previous, str(first_applyid or ""))
        sheet_result = write_agency_sheet_for_record(record_id)
        log_event({"step": "agency_sheet_after_run", "record_id": record_id, **sheet_result})
    except Exception as exc:
        log_event(
            {
                "step": "agency_sheet_after_run",
                "ok": False,
                "record_id": record_id,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )


# Place in China as pinyin (province, city, district), the only source of the
# invite / arrival / stay / departure place (both regions), by visa type:
#   M (inviting company), F / X1 / X2 (school):
#       provinceNamePinyin / cityNamePinyin / districtNamePinyin
#   others, e.g. Q1 / Q2 / S2 (inviter):
#       inviterProvincePinyin / inviterCityPinyin / inviterDistrictPinyin
_ORGANIZATION_LOCATION_PINYIN_KEYS = (
    "provinceNamePinyin",
    "cityNamePinyin",
    "districtNamePinyin",
)
_INVITER_LOCATION_PINYIN_KEYS = (
    "inviterProvincePinyin",
    "inviterCityPinyin",
    "inviterDistrictPinyin",
)
_ORGANIZATION_VISA_PREFIXES = ("M", "F", "X")


def _location_pinyin(case: dict[str, Any]) -> tuple[str, str, str]:
    visa_type = str(case.get("visa_type", "") or "").strip().upper()
    keys = (
        _ORGANIZATION_LOCATION_PINYIN_KEYS
        if visa_type.startswith(_ORGANIZATION_VISA_PREFIXES)
        else _INVITER_LOCATION_PINYIN_KEYS
    )
    return tuple(str(case.get(key, "") or "").strip() for key in keys)


def _run_status_code(result: dict[str, Any]) -> int:
    if result.get("ok"):
        return 200
    if result.get("step") == "validate":
        return 422
    if result.get("status_code") is None and result.get("response") is None:
        # Local failure (exception, missing file…), not an upstream answer.
        return 500
    return 502


@app.get("/visa-registrations/sync-draft-status")
async def sync_draft_visa_status(
    page_num: int = 1,
    page_size: int = 1000,
    authorization: str = "",
    spreadsheet_url: str = "",
    worksheet_name: str = "",
    sheet_mode: str = "upsert",
    statuses: str = "",
    max_records: int | None = None,
    concurrency: int = 5,
    skip_google_sheet: bool = False,
):
    if not _is_sync_draft_enabled():
        return {
            "ok": False,
            "disabled": True,
            "message": "sync_draft is disabled",
        }

    started_at = time.perf_counter()
    print(
        "[sync_draft_route] request "
        f"page_num={page_num} page_size={page_size} "
        f"statuses={statuses or 'default'} max_records={max_records} "
        f"concurrency={concurrency} skip_google_sheet={skip_google_sheet}",
        flush=True,
    )
    if authorization.strip():
        append_authorization(authorization)
    result = await asyncio.to_thread(
        asyncio.run,
        sync_draft_visa_registrations(
            page_num=page_num,
            page_size=page_size,
            authorization=authorization,
            spreadsheet_url=spreadsheet_url,
            # Same tab as the scheduler unless the caller names one.
            worksheet_name=worksheet_name.strip()
            or os.getenv("GOOGLE_SHEET_SYNC_WORKSHEET", "hai").strip(),
            sheet_mode=sheet_mode,
            statuses=statuses or None,
            max_records=max_records,
            concurrency=concurrency,
            skip_google_sheet=skip_google_sheet,
        ),
    )
    print(
        "[sync_draft_route] response "
        f"matched={result.get('matched', 0)} updated={result.get('updated', 0)} "
        f"skipped={result.get('skipped', 0)} "
        f"display_only={result.get('display_only', 0)} "
        f"duration={time.perf_counter() - started_at:.2f}s",
        flush=True,
    )
    return result


@app.post("/agency/reassign")
def agency_reassign(payload: dict[str, Any] = Body(...)):
    """
    Move a registration to another agency, e.g. one run with an old-style
    source_prefix ("L15-HOANG VAN A") that landed in CHUNG.
    Body: {"agency_code": "MAI", "first_applyid": "..."} or
          {"agency_code": "MAI", "passport_number": "E05111310"} (latest one);
          optional "agency_name".
    """
    result = reassign_agency(
        agency_code=str(payload.get("agency_code", "") or ""),
        first_applyid=str(payload.get("first_applyid", "") or ""),
        passport_number=str(payload.get("passport_number", "") or ""),
        agency_name=str(payload.get("agency_name", "") or ""),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/agency/merge-small")
def agency_merge_small(payload: dict[str, Any] = Body(default={})):
    """South: merge small idle agencies (< 5 records, nothing new for 14 days) into CHUNG.
    Body {"dry_run": true} only lists them. Also runs by itself once a day."""
    dry_run = str((payload or {}).get("dry_run", "")).strip().lower() in {"1", "true", "yes"}
    return merge_small_agencies(dry_run=dry_run)


@app.post("/google-sheets/debug")
def debug_google_sheets(payload: dict[str, Any] = Body(...)):
    spreadsheet_url = str(
        payload.get("spreadsheet_url", "") or payload.get("url", "")
    ).strip()
    worksheet_name = str(
        payload.get("worksheet_name", "") or payload.get("sheet_name", "")
    ).strip()
    if not spreadsheet_url:
        raise HTTPException(status_code=400, detail="spreadsheet_url is required")
    return debug_google_sheet_access(
        spreadsheet_url=spreadsheet_url,
        worksheet_name=worksheet_name,
    )


@app.api_route("/convert-input-pdfs", methods=["GET", "POST"])
async def convert_input_pdfs(request: Request, key: str = Query("")):
    # GET: ?key=...  (body của GET hay bị proxy/client bỏ đi)
    # POST: {"key": "..."} hoặc ?key=...
    download_key = key.strip()
    if not download_key:
        raw_body = await request.body()
        try:
            body_json = json.loads(raw_body) if raw_body else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            body_json = None
        if isinstance(body_json, dict):
            download_key = str(body_json.get("key", "")).strip()

    # Tải R2 + render PDF đều là blocking I/O/CPU -> chạy ngoài event loop.
    return await asyncio.to_thread(api_convert_input_pdfs, download_key=download_key)


@app.post("/convert-input-pdfs/cleanup")
def convert_input_pdfs_cleanup(payload: dict[str, Any] = Body(default_factory=dict)):
    # Gọi sau khi đã merge ảnh lại thành PDF:
    # {"key": "folder/x.pdf"}  -> xóa mọi folder/x_page_N.png
    # {"keys": ["output/..._page_1.png", ...]}  -> xóa đúng các ảnh này
    raw_keys = payload.get("keys") or []
    result = api_cleanup_pdf_page_images(
        pdf_key=str(payload.get("key", "") or ""),
        keys=raw_keys if isinstance(raw_keys, list) else [raw_keys],
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.get("/han-approval/process")
async def han_approval_process(
    start_scan: str = Query("", alias="start-scan"),
    end_scan: str = Query("", alias="end-scan"),
    authorization: str = Query("", alias="authorization"),
):
    return await process_han_approval_inbox(
        start_scan=start_scan,
        end_scan=end_scan,
        authorization=authorization,
    )


@app.post("/han-approval/process-by-passports")
async def han_approval_process_by_passports(
    payload: dict[str, Any] = Body(...),
    start_scan: str = Query("", alias="start-scan"),
    end_scan: str = Query("", alias="end-scan"),
    authorization: str = Query("", alias="authorization"),
):
    raw_passport_numbers = payload.get("passport_numbers")
    if isinstance(raw_passport_numbers, str):
        raw_passport_numbers = raw_passport_numbers.split(",")
    if not isinstance(raw_passport_numbers, list):
        raise HTTPException(
            status_code=400,
            detail="passport_numbers must be an array or a comma-separated string",
        )

    passport_numbers = list(
        dict.fromkeys(
            str(passport_number or "").strip().upper()
            for passport_number in raw_passport_numbers
            if str(passport_number or "").strip()
        )
    )
    if not passport_numbers:
        raise HTTPException(status_code=400, detail="passport_numbers is required")

    return await process_han_approval_inbox(
        start_scan=start_scan,
        end_scan=end_scan,
        authorization=authorization,
        passport_numbers=passport_numbers,
    )


@app.get("/han-approval/jobs")
def han_approval_jobs(limit: int = 100, offset: int = 0):
    return list_han_approval_jobs(limit=limit, offset=offset)


@app.patch("/han-approval/reset-printed-status")
def han_approval_reset_printed_status(
    start: str = Query("", alias="start"),
    end: str = Query("", alias="end"),
):
    return reset_han_approval_printed_status(start=start, end=end)


@app.patch("/han-approval/retry")
def han_approval_retry(payload: dict[str, Any] = Body(...)):
    record_ids = payload.get("record_ids") or payload.get("ids") or []
    han_codes = payload.get("han_codes") or payload.get("codes") or []
    if not record_ids and not han_codes:
        raise HTTPException(
            status_code=400,
            detail="record_ids or han_codes is required",
        )
    return retry_han_approval_jobs(
        record_ids=record_ids,
        han_codes=han_codes,
    )


_WEASYPRINT_LOCK = threading.Lock()


def _render_html_and_upload(html_content: bytes, folder_name: str, filename: str) -> str:
    started_at = time.perf_counter()
    # WeasyPrint (Pango/fontconfig) không đảm bảo thread-safe -> render lần lượt.
    with _WEASYPRINT_LOCK:
        waited_at = time.perf_counter()
        pdf_path = convert_html_to_pdf(html_content)
    rendered_at = time.perf_counter()
    r2_key = upload_pdf_to_r2(pdf_path, f"{folder_name}/")
    log_event(
        {
            "step": "timing",
            "phase": "html_to_pdf",
            "filename": filename,
            "html_bytes": len(html_content),
            "lock_wait_seconds": round(waited_at - started_at, 2),
            "render_seconds": round(rendered_at - waited_at, 2),
            "upload_seconds": round(time.perf_counter() - rendered_at, 2),
            "key": r2_key,
        }
    )
    return r2_key


@app.post("/upload-html-to-pdf")
async def upload_html_to_pdf(file: UploadFile = File(...), folderName: str = Form(...)):
    try:
        if not file.filename.endswith(".html"):
            raise HTTPException(status_code=400, detail="File must be .html")

        html_content = await file.read()
        # WeasyPrint render + upload R2 đều blocking -> chạy ngoài event loop.
        r2_key = await asyncio.to_thread(
            _render_html_and_upload, html_content, folderName, file.filename
        )

        return {"message": "Upload thanh cong", "file_key": r2_key}

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        log_exception(e, {"path": "/upload-html-to-pdf", "filename": file.filename})
        if _is_debug_enabled():
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": type(e).__name__,
                    "message": str(e),
                    "traceback": tb,
                },
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/r2/images")
async def r2_images(
    request: Request,
    mode: str = Form("upload"),
    folder: str = Form(""),
    key: str = Form(""),
    filename: str = Form(""),
    content_type: str = Form(""),
    expires_in: int = Form(900),
    image_base64: str = Form(""),
    file: UploadFile | None = File(None),
):
    file_bytes = await file.read() if file is not None else None
    result = await asyncio.to_thread(
        api_sign_and_push_image_to_r2,
        mode=mode,
        folder=folder,
        key=key,
        filename=filename,
        content_type=content_type,
        expires_in=expires_in,
        image_base64=image_base64,
        file_bytes=file_bytes,
        file_name=file.filename if file is not None else "",
        file_content_type=file.content_type if file is not None else "",
    )
    result["request"] = {
        "method": request.method,
        "mode": mode,
        "folder": folder,
        "key": key,
        "filename": filename,
        "content_type": content_type,
        "expires_in": expires_in,
        "has_file": file is not None,
    }
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/r2/images/delete")
def r2_images_delete(payload: dict[str, Any] = Body(...)):
    key = str(payload.get("key", "") or "").strip()
    prefix = str(payload.get("prefix", "") or "").strip()
    result = api_delete_r2_objects(key=key, prefix=prefix)
    result["request"] = {
        "key": key,
        "prefix": prefix,
    }
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/r2/folders/archive")
def r2_folders_archive(payload: dict[str, Any] = Body(...)):
    # WF14: move the input folder to _archive/<stamp>__<PASSPORT>/ (lifecycle deletes it after 7 days).
    prefix = str(payload.get("prefix", "") or "").strip()
    result = api_archive_r2_folder(prefix, str(payload.get("passport_number", "") or ""))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/r2/folders/restore")
def r2_folders_restore(payload: dict[str, Any] = Body(...)):
    # WF-15: clear <passport>/ output and move the latest archive back. confirm=false = dry run.
    result = api_restore_r2_folder(
        str(payload.get("prefix", "") or ""),
        str(payload.get("passport_number", "") or ""),
        confirm=str(payload.get("confirm", "")).strip().lower() in ("true", "1", "yes"),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.get("/r2/images/get")
def r2_images_get(
    key: str = Query(""),
    download: bool = Query(False),
):
    result = api_download_r2_object_bytes(key)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)

    content = result.get("content", b"")
    content_type = str(result.get("content_type") or "application/octet-stream")
    filename = key.rsplit("/", 1)[-1] if key else "file"
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return Response(
        content=content,
        media_type=content_type,
        headers=headers,
    )


@app.get("/r2/folders/download")
def r2_folders_download(prefix: str = Query(""), scan: bool = Query(False)):
    # scan=1: flatten document photos like a scanner. South only for now.
    do_scan = scan and REGION == REGION_SOUTH
    result = api_download_r2_folder_zip(prefix, scan=do_scan)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)

    content = result.get("content", b"")
    prefix_text = str(result.get("prefix") or prefix or "").rstrip("/")
    folder_name = prefix_text.rsplit("/", 1)[-1] if prefix_text else "r2-folder"
    headers = {
        "Content-Disposition": f'attachment; filename="{folder_name}.zip"',
        "X-R2-File-Count": str(result.get("file_count", 0)),
        "X-R2-Total-Size": str(result.get("total_size", 0)),
        "X-Scan-Applied": "1" if do_scan else "0",
    }
    return Response(
        content=content,
        media_type="application/zip",
        headers=headers,
    )


@app.post("/pdf-to-images")
def pdf_to_images(file: UploadFile = File(...)):
    pdf_bytes = file.file.read()
    batch_id = uuid.uuid4()
    with ThreadPoolExecutor(max_workers=8) as pool:
        result = render_pdf_pages_to_r2(
            pdf_bytes, lambda n: f"output/{batch_id}_page_{n}.png", pool
        )
    if not result.get("ok"):
        status = 400 if result.get("error") == "invalid_pdf" else 502
        raise HTTPException(status_code=status, detail=result)

    images = [
        {
            "page": item["page"],
            "key": item["key"],
            "url": item["url"] or item["key"],
        }
        for item in result["uploaded_pngs"]
    ]

    return {
        "count": len(images),
        "images": images,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=_server_port(),
        reload=False,
    )
