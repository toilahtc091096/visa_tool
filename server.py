import asyncio
import json
import os
import time
import traceback
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Body, Form, Query
from fastapi.responses import JSONResponse, Response
from pdf2image import convert_from_bytes
import io
import uuid

from api import api_convert_input_pdfs
from api import api_download_r2_folder_zip
from api import api_download_r2_object_bytes
from api import api_delete_r2_objects
from api import api_sign_and_push_image_to_r2
from database.connection import init_database
from main import build_case, main
from services.han_approval import (
    list_han_approval_jobs,
    process_han_approval_inbox,
    reset_han_approval_printed_status,
    retry_han_approval_jobs,
)
from services import sync_draft_visa_registrations
from services.google_sheets import debug_google_sheet_access
from utils import convert_html_to_pdf, log_exception, upload_pdf_to_r2
from utils.r2_env import build_r2_client
from utils.token_store import append_authorization

print("START", flush=True)


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


def _server_port() -> int:
    raw_value = os.getenv("PORT", "10000").strip()
    try:
        return int(raw_value)
    except ValueError:
        return 10000


async def _sync_draft_scheduler_loop() -> None:
    interval_seconds = _sync_scheduler_interval_seconds()
    spreadsheet_url = os.getenv("GOOGLE_SHEET_SYNC_URL", "").strip()
    worksheet_name = os.getenv("GOOGLE_SHEET_SYNC_WORKSHEET", "hai").strip()
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
                f"skipped={result.get('skipped', 0)} "
                f"display_only={result.get('display_only', 0)}"
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
    worksheet_name: str = "hai",
    sheet_mode: str = "upsert",
    statuses: str = "",
    max_records: int | None = None,
    concurrency: int = 5,
    skip_google_sheet: bool = False,
):
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
    result = await sync_draft_visa_registrations(
        page_num=page_num,
        page_size=page_size,
        authorization=authorization,
        spreadsheet_url=spreadsheet_url,
        worksheet_name=worksheet_name,
        sheet_mode=sheet_mode,
        statuses=statuses or None,
        max_records=max_records,
        concurrency=concurrency,
        skip_google_sheet=skip_google_sheet,
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


@app.post("/upload-html-to-pdf")
async def upload_html_to_pdf(file: UploadFile = File(...), folderName: str = Form(...)):
    try:
        if not file.filename.endswith(".html"):
            raise HTTPException(status_code=400, detail="File must be .html")

        html_content = await file.read()
        pdf_path = convert_html_to_pdf(html_content)
        r2_key = upload_pdf_to_r2(
            pdf_path,
            f"{folderName}/lich_su_xuat_canh/chua_tung_di_ho_chieu_trang/giay_cu_tru/",
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
    result = api_sign_and_push_image_to_r2(
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
def r2_folders_download(prefix: str = Query("")):
    result = api_download_r2_folder_zip(prefix)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)

    content = result.get("content", b"")
    prefix_text = str(result.get("prefix") or prefix or "").rstrip("/")
    folder_name = prefix_text.rsplit("/", 1)[-1] if prefix_text else "r2-folder"
    headers = {
        "Content-Disposition": f'attachment; filename="{folder_name}.zip"',
        "X-R2-File-Count": str(result.get("file_count", 0)),
        "X-R2-Total-Size": str(result.get("total_size", 0)),
    }
    return Response(
        content=content,
        media_type="application/zip",
        headers=headers,
    )


@app.post("/pdf-to-images")
async def pdf_to_images(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    pages = convert_from_bytes(
        pdf_bytes, dpi=300, poppler_path="C:/poppler-26.02.0/Library/bin"
    )

    images = []
    public_base = os.getenv("R2_PUBLIC_BASE", "").rstrip("/")
    _r2_s3_client, r2_config = build_r2_client(log=True)

    for page_number, page in enumerate(pages, start=1):
        buffer = io.BytesIO()
        page.save(buffer, format="PNG")
        buffer.seek(0)

        key = f"output/{uuid.uuid4()}_page_{page_number}.png"
        _r2_s3_client.upload_fileobj(
            buffer,
            r2_config.bucket_name,
            key,
            ExtraArgs={"ContentType": "image/png"},
        )

        images.append(
            {
                "page": page_number,
                "key": key,
                "url": f"{public_base}/{key}" if public_base else key,
            }
        )

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
