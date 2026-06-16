import asyncio
import json
import os
import traceback
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Body, Form
from fastapi.responses import JSONResponse

from api import api_convert_input_pdfs
from database.connection import init_database
from main import build_case, main
from services import sync_draft_visa_registrations
from services.google_sheets import debug_google_sheet_access
from utils import convert_html_to_pdf, log_exception, upload_pdf_to_r2
from utils.token_store import append_authorization

def _is_debug_enabled() -> bool:
    value = os.getenv("DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_sync_scheduler_enabled() -> bool:
    value = os.getenv("SYNC_DRAFT_SCHEDULER_ENABLED", "1").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _sync_scheduler_interval_seconds() -> int:
    raw_value = os.getenv("SYNC_DRAFT_SCHEDULER_INTERVAL_SECONDS", "").strip()
    if not raw_value:
        return 12 * 60 * 60
    try:
        return max(60, int(raw_value))
    except ValueError:
        return 12 * 60 * 60


async def _sync_draft_scheduler_loop() -> None:
    interval_seconds = _sync_scheduler_interval_seconds()
    spreadsheet_url = os.getenv("GOOGLE_SHEET_SYNC_URL", "").strip()
    worksheet_name = os.getenv("GOOGLE_SHEET_SYNC_WORKSHEET", "sync_draft_visa_status").strip()
    sheet_mode = os.getenv("GOOGLE_SHEET_SYNC_MODE", "upsert").strip()

    while True:
        try:
            result = await sync_draft_visa_registrations(
                spreadsheet_url=spreadsheet_url,
                worksheet_name=worksheet_name,
                sheet_mode=sheet_mode,
            )
            print(
                "[sync_draft_scheduler] completed "
                f"matched={result.get('matched', 0)} "
                f"updated={result.get('updated', 0)} "
                f"skipped={result.get('skipped', 0)}"
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    scheduler_task = None
    if _is_sync_scheduler_enabled():
        scheduler_task = asyncio.create_task(_sync_draft_scheduler_loop())
    yield
    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run")
def run(payload: dict[str, Any] = Body(...)):
    authorization = str(payload.get("authorization", "") or "").strip()
    if authorization:
        append_authorization(authorization)
    case = build_case(payload)
    main(
        case,
        first_applyid=case.get("first_applyid", ""),
        is_update_info=case.get("is_update_info", False),
        upload_config_keys=case.get("upload_config_keys", []),
    )
    return {"ok": True, "received": payload is not None}


@app.get("/visa-registrations/sync-draft-status")
async def sync_draft_visa_status(
    page_num: int = 1,
    page_size: int = 1000,
    authorization: str = "",
    spreadsheet_url: str = "",
    worksheet_name: str = "sync_draft_visa_status",
    sheet_mode: str = "upsert",
):
    if authorization.strip():
        append_authorization(authorization)
    return await sync_draft_visa_registrations(
        page_num=page_num,
        page_size=page_size,
        authorization=authorization,
        spreadsheet_url=spreadsheet_url,
        worksheet_name=worksheet_name,
        sheet_mode=sheet_mode,
    )


@app.post("/google-sheets/debug")
def debug_google_sheets(payload: dict[str, Any] = Body(...)):
    spreadsheet_url = str(payload.get("spreadsheet_url", "") or payload.get("url", "")).strip()
    worksheet_name = str(payload.get("worksheet_name", "") or payload.get("sheet_name", "")).strip()
    if not spreadsheet_url:
        raise HTTPException(status_code=400, detail="spreadsheet_url is required")
    return debug_google_sheet_access(
        spreadsheet_url=spreadsheet_url,
        worksheet_name=worksheet_name,
    )


@app.api_route("/convert-input-pdfs", methods=["GET", "POST"])
async def convert_input_pdfs(request: Request):
    raw_body = await request.body()
    body_text = raw_body.decode("utf-8", errors="replace") if raw_body else ""
    try:
        body_json = json.loads(body_text) if body_text else None
    except json.JSONDecodeError:
        body_json = None

    download_key = ""
    if isinstance(body_json, dict):
        download_key = str(body_json.get("key", "")).strip()

    result = api_convert_input_pdfs(download_key=download_key)
    result["request"] = {
        "method": request.method,
        "body_text": body_text,
        "body_json": body_json,
    }
    return result


@app.post("/upload-html-to-pdf")
async def upload_html_to_pdf(file: UploadFile = File(...),
    folderName: str = Form(...)):
    try:
        if not file.filename.endswith(".html"):
            raise HTTPException(status_code=400, detail="File must be .html")

        html_content = await file.read()
        pdf_path = convert_html_to_pdf(html_content)
        r2_key = upload_pdf_to_r2(pdf_path, f"{folderName}/lich_su_xuat_canh/chua_tung_di_ho_chieu_trang/giay_cu_tru/")

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
