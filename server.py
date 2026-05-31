import json
from fastapi import FastAPI, Request
from typing import Any
from api import api_convert_input_pdfs
from main import build_case, main
app = FastAPI()

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

    result = api_convert_input_pdfs()
    result["request"] = {
        "method": request.method,
        "body_text": body_text,
        "body_json": body_json,
    }
    return result
