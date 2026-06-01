import json
import os
import traceback
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from api import api_convert_input_pdfs
from main import build_case, main
from utils import convert_html_to_pdf, log_exception, upload_pdf_to_r2

app = FastAPI()


def _is_debug_enabled() -> bool:
    value = os.getenv("DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run")
def run(payload: dict[str, Any] | None = None):
    case = build_case(payload)
    main(
        case,
        first_applyid=case.get("first_applyid", ""),
        is_update_info=case.get("is_update_info", False),
        upload_config_keys=case.get("upload_config_keys", []),
    )
    return {"ok": True, "received": payload is not None}


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
async def upload_html_to_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".html"):
            raise HTTPException(status_code=400, detail="File must be .html")

        html_content = await file.read()
        pdf_path = convert_html_to_pdf(html_content)
        r2_key = upload_pdf_to_r2(pdf_path)

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
