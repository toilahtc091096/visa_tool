"""Logic behind the /web input form: validate the form, build the same payload
that WF-01 node 2 used to build by hand, start n8n, and prepare a re-run."""

from __future__ import annotations

import os
import re
import secrets
import string
from typing import Any

import requests

# House -> bucket and server instance (one Python instance per house on the VPS).
HOUSES: dict[str, dict[str, str]] = {
    "HAI": {"bucket": "visa-data", "api_port": "10000"},
    "PHONG": {"bucket": "visa-data-phong", "api_port": "20000"},
    "TAI": {"bucket": "visa-data-tai", "api_port": "30000"},
}

VISA_CODES = ["L", "M", "Q1", "Q2", "F", "X1", "X2", "S2"]

RELATIONS = [
    ("spouse", "Vợ/chồng"),
    ("parents", "Cha mẹ"),
    ("spouseParents", "Cha mẹ vợ/chồng"),
    ("children", "Con cái"),
    ("siblings", "Anh chị em"),
    ("paternalGrandparents", "Ông bà nội"),
    ("maternalGrandparents", "Ông bà ngoại"),
    ("grandchildren", "Cháu (nội)"),
    ("maternalGrandchildren", "Cháu (ngoại)"),
    ("childrenSpouse", "Con dâu/con rể"),
    ("relative", "Họ hàng"),
]
_RELATION_KEYS = {k for k, _ in RELATIONS}
_RELATION_REQUIRED = {"Q1", "Q2"}


class FormError(ValueError):
    """A message for the person filling the form."""


def build_visa_type(code: str, days: str) -> str:
    """Join code + days the way normalize_visa_type expects (L+30 -> L30, Q2+180 -> Q2180)."""
    code = str(code or "").strip().upper()
    days = str(days or "").strip()
    if code not in VISA_CODES:
        raise FormError(f"Loại visa không hợp lệ: {code or '(trống)'}")
    if days and not days.isdigit():
        raise FormError("Số ngày chỉ được nhập số")
    n = int(days) if days else 0
    if code == "L" and days not in ("15", "30"):
        raise FormError("Visa L: số ngày phải là 15 hoặc 30")
    if code in ("M", "F") and days and days not in ("15", "30", "90"):
        raise FormError(f"Visa {code}: số ngày phải là 15, 30 hoặc 90 (để trống = mặc định)")
    if code == "X1" and days and n <= 180:
        raise FormError("Visa X1: số ngày phải lớn hơn 180")
    if code == "X2" and days and not 1 <= n <= 180:
        raise FormError("Visa X2: số ngày từ 1 đến 180")
    return code + days


def normalize_source_prefix(value: str) -> str:
    text = str(value or "").strip().strip("/").strip()
    if not text:
        raise FormError("Chưa nhập thư mục hồ sơ")
    if text.startswith("_archive") or ".." in text:
        raise FormError("Thư mục hồ sơ không hợp lệ")
    return text + "/"


def house_config(house: str) -> dict[str, str]:
    key = str(house or "").strip().upper()
    if key not in HOUSES:
        raise FormError(f"Nhà không hợp lệ: {house or '(trống)'}")
    return {"house": key, **HOUSES[key]}


def new_job_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "job-" + "".join(secrets.choice(alphabet) for _ in range(8))


def build_start_payload(staff_code: str, form: dict[str, Any]) -> dict[str, str]:
    """Same fields WF-01 node 2 sends to WF01-GENERAL."""
    house = house_config(form.get("house"))
    visa_code = str(form.get("visa_code") or "").strip().upper()
    visa_type = build_visa_type(visa_code, form.get("days"))
    relation = str(form.get("relation") or "").strip()
    if relation and relation not in _RELATION_KEYS:
        raise FormError(f"Quan hệ không hợp lệ: {relation}")
    if visa_code in _RELATION_REQUIRED and not relation:
        raise FormError(f"Visa {visa_code}: phải chọn quan hệ (người mời là gì của người xin visa)")
    return {
        "job_id": new_job_id(),
        "staff": str(staff_code or "").strip().upper(),
        "house": house["house"],
        "bucket": house["bucket"],
        "api_port": house["api_port"],
        "visa_type": visa_type,
        "relation": relation,
        "source_prefix": normalize_source_prefix(form.get("source_prefix")),
        "folder_name": "t",
    }


def start_case(payload: dict[str, str]) -> dict[str, Any]:
    """POST the payload to the n8n webhook of WF-00 Web Start."""
    url = os.getenv("N8N_START_WEBHOOK_URL", "").strip()
    if not url:
        raise RuntimeError("Chưa cấu hình N8N_START_WEBHOOK_URL trong .env")
    resp = requests.post(
        url,
        json=payload,
        headers={"X-Api-Key": os.getenv("VISA_API_KEY", "").strip()},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"n8n trả lỗi {resp.status_code}: {resp.text[:300]}")
    return {"ok": True, "job_id": payload["job_id"]}


def rerun_prepare(form: dict[str, Any]) -> dict[str, Any]:
    """Call /r2/folders/restore on the instance of the chosen house (local call, no key needed)."""
    house = house_config(form.get("house"))
    passport = str(form.get("passport_number") or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,12}", passport):
        raise FormError("Số hộ chiếu không hợp lệ (6–12 chữ hoa và số)")
    body = {
        "prefix": normalize_source_prefix(form.get("source_prefix")),
        "passport_number": passport,
        "confirm": bool(form.get("confirm")),
    }
    resp = requests.post(f"http://127.0.0.1:{house['api_port']}/r2/folders/restore", json=body, timeout=120)
    try:
        data = resp.json()
    except ValueError:
        data = {"ok": False, "error": resp.text[:300]}
    if resp.status_code >= 400:
        detail = data.get("detail", data) if isinstance(data, dict) else data
        return {"ok": False, **(detail if isinstance(detail, dict) else {"error": str(detail)})}
    return data


def form_options() -> dict[str, Any]:
    return {
        "houses": list(HOUSES),
        "visa_codes": VISA_CODES,
        "relations": [{"value": k, "label": v} for k, v in RELATIONS],
        "relation_required": sorted(_RELATION_REQUIRED),
    }
