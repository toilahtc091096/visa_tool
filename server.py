print("1")

from fastapi import FastAPI

print("2")

from api import api_convert_input_pdfs

print("3")

from main import build_case, main

print("4")

app = FastAPI()

print("5")

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
def convert_input_pdfs():
    return api_convert_input_pdfs()
