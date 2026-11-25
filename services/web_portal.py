"""Logic behind the /web input form: validate the form, build the same payload
that WF-01 node 2 used to build by hand, start n8n, and prepare a re-run."""

from __future__ import annotations

import os
import re
from io import BytesIO
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

# Inviter relation = what the INVITER is to the applicant. value goes as-is into the curl
# (WF-12 passes an upper-case label through) and must be a label the server knows
# (constants.INVITER_RELATION_ZH_SOUTH: "chong" -> 丈夫, "vo sap cuoi" -> 未婚妻 ...).
# (value, label shown, example). "first_for" = visa codes that list it at the top.
RELATIONS = [
    {"value": "CHONG", "label": "Chồng", "example": "chồng mời vợ"},
    {"value": "VO", "label": "Vợ", "example": "vợ mời chồng"},
    {"value": "CHONG SAP CUOI", "label": "Chồng sắp cưới", "example": "chồng sắp cưới mời vợ sắp cưới", "first_for": ["S2"]},
    {"value": "VO SAP CUOI", "label": "Vợ sắp cưới", "example": "vợ sắp cưới mời chồng sắp cưới", "first_for": ["S2"]},
    {"value": "BO", "label": "Bố", "example": "bố mời con"},
    {"value": "ME", "label": "Mẹ", "example": "mẹ mời con"},
    {"value": "CON TRAI", "label": "Con trai", "example": "con trai mời bố / mẹ"},
    {"value": "CON GAI", "label": "Con gái", "example": "con gái mời bố / mẹ"},
    {"value": "CON RE", "label": "Con rể", "example": "con rể mời bố / mẹ vợ"},
    {"value": "CON DAU", "label": "Con dâu", "example": "con dâu mời bố / mẹ chồng"},
    {"value": "BO VO", "label": "Bố vợ", "example": "bố vợ mời con rể"},
    {"value": "ME VO", "label": "Mẹ vợ", "example": "mẹ vợ mời con rể"},
    {"value": "BO CHONG", "label": "Bố chồng", "example": "bố chồng mời con dâu"},
    {"value": "ME CHONG", "label": "Mẹ chồng", "example": "mẹ chồng mời con dâu"},
    {"value": "ANH TRAI", "label": "Anh trai", "example": "anh trai mời em"},
    {"value": "CHI GAI", "label": "Chị gái", "example": "chị gái mời em"},
    {"value": "EM TRAI", "label": "Em trai", "example": "em trai mời anh / chị"},
    {"value": "EM GAI", "label": "Em gái", "example": "em gái mời anh / chị"},
    {"value": "ONG NOI", "label": "Ông nội", "example": "ông nội mời cháu"},
    {"value": "BA NOI", "label": "Bà nội", "example": "bà nội mời cháu"},
    {"value": "ONG NGOAI", "label": "Ông ngoại", "example": "ông ngoại mời cháu"},
    {"value": "BA NGOAI", "label": "Bà ngoại", "example": "bà ngoại mời cháu"},
    {"value": "CHAU NOI", "label": "Cháu nội", "example": "cháu nội mời ông / bà nội"},
    {"value": "CHAU NGOAI", "label": "Cháu ngoại", "example": "cháu ngoại mời ông / bà ngoại"},
    {"value": "CHA DUONG", "label": "Cha dượng", "example": "cha dượng mời con riêng của vợ"},
    {"value": "ME KE", "label": "Mẹ kế", "example": "mẹ kế mời con riêng của chồng"},
    {"value": "CON TRAI RIENG", "label": "Con trai riêng", "example": "con trai riêng (của vợ / chồng) mời cha dượng / mẹ kế"},
    {"value": "CON GAI RIENG", "label": "Con gái riêng", "example": "con gái riêng (của vợ / chồng) mời cha dượng / mẹ kế"},
    {"value": "ANH RE", "label": "Anh rể", "example": "anh rể (chồng của chị) mời em"},
    {"value": "EM RE", "label": "Em rể", "example": "em rể (chồng của em gái) mời anh / chị"},
    {"value": "CHI DAU", "label": "Chị dâu", "example": "chị dâu (vợ của anh) mời em"},
    {"value": "EM DAU", "label": "Em dâu", "example": "em dâu (vợ của em trai) mời anh / chị"},
    {"value": "CHU", "label": "Chú", "example": "chú (em trai của bố) mời cháu"},
    {"value": "BAC", "label": "Bác", "example": "bác (anh của bố) mời cháu"},
    {"value": "CO", "label": "Cô", "example": "cô (chị / em gái của bố) mời cháu"},
    {"value": "CAU", "label": "Cậu", "example": "cậu (anh / em trai của mẹ) mời cháu"},
    {"value": "DI", "label": "Dì", "example": "dì (chị / em gái của mẹ) mời cháu"},
    {"value": "HO HANG", "label": "Họ hàng", "example": "họ hàng khác mời"},
]
_RELATION_KEYS = {r["value"] for r in RELATIONS}
_RELATION_REQUIRED = {"Q1", "Q2"}
# Every visa: the applicant's phone (optional) goes into the curl as `phone`.
# Visit visas (A invites B): it is required and also payMobile; the Chinese inviter's
# phone is required too (inviterPhone).
PHONE_REQUIRED = {"Q1", "Q2", "S2"}


class FormError(ValueError):
    """A message for the person filling the form."""


def clean_phone(value: Any, label: str) -> str:
    """Digits only (a leading + is kept); spaces, dots and dashes are dropped."""
    raw = str(value or "").strip()
    plus = raw.startswith("+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    if not 8 <= len(digits) <= 15 or any(not (ch.isdigit() or ch in " .-()+") for ch in raw):
        raise FormError(f"{label} không hợp lệ: {raw}")
    return ("+" if plus else "") + digits


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
    inviter_phone = pay_mobile = ""
    if visa_code in PHONE_REQUIRED:
        inviter_phone = clean_phone(form.get("inviter_phone"), "Số điện thoại người mời (bên Trung)")
        pay_mobile = clean_phone(form.get("phone") or form.get("pay_mobile"), "Số điện thoại người được mời (bên Việt)")
        if not inviter_phone or not pay_mobile:
            raise FormError(f"Visa {visa_code}: phải điền 2 số điện thoại (người mời bên Trung, người được mời bên Việt)")
        phone = pay_mobile
    else:
        phone = clean_phone(form.get("phone"), "Số điện thoại người khai")
    return {
        "job_id": new_job_id(),
        "staff": str(staff_code or "").strip().upper(),
        "house": house["house"],
        "bucket": house["bucket"],
        "api_port": house["api_port"],
        "visa_type": visa_type,
        "relation": relation,
        "inviter_phone": inviter_phone,
        "pay_mobile": pay_mobile,
        "phone": phone,
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


_RESTORE_ERRORS = {
    "archive_not_found_for_passport": "Nhà {house}: không có bản lưu trữ của hộ chiếu {passport}. "
                                      "Nếu hồ sơ chưa chạy xong hoặc chạy trước 20/11/2026, nhập thêm tên thư mục.",
    "nothing_to_restore": "Nhà {house}: không có thư mục gốc lẫn bản lưu trữ của thư mục này.",
    "source_and_archive_both_exist": "Nhà {house}: thư mục gốc vẫn còn và cũng có bản lưu trữ — kiểm tra trên R2 trước.",
    "invalid_passport_number": "Số hộ chiếu không hợp lệ.",
    "invalid_prefix": "Tên thư mục không hợp lệ.",
}


def rerun_prepare(form: dict[str, Any]) -> dict[str, Any]:
    """Call /r2/folders/restore on the instance of the house (local call, no key needed).
    Only the passport number is required: the folder comes from the archive name
    (`_archive/<stamp>__<PASSPORT>/`). Without a house, every house is searched (dry run)."""
    passport = str(form.get("passport_number") or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,12}", passport):
        raise FormError("Số hộ chiếu không hợp lệ (6–12 chữ hoa và số)")
    raw_prefix = str(form.get("source_prefix") or "").strip()
    prefix = normalize_source_prefix(raw_prefix) if raw_prefix.strip("/ ") else ""
    confirm = bool(form.get("confirm"))

    def ask(house: dict[str, str], do_it: bool) -> dict[str, Any]:
        body = {"prefix": prefix, "passport_number": passport, "confirm": do_it}
        resp = requests.post(_local(house, "/r2/folders/restore"), json=body, timeout=120)
        r = {**_json_or_error(resp), "house": house["house"]}
        if not r.get("ok") and r.get("error") in _RESTORE_ERRORS:
            r["error"] = _RESTORE_ERRORS[r["error"]].format(house=house["house"], passport=passport)
        return r

    if str(form.get("house") or "").strip():
        return ask(house_config(form.get("house")), confirm)

    if confirm:
        raise FormError("Bấm Kiểm tra trước để tìm ra nhà của hồ sơ")
    found = []
    for name in HOUSES:
        try:
            r = ask(house_config(name), False)
        except requests.RequestException:
            continue
        if r.get("ok"):
            found.append(r)
    if not found:
        return {"ok": False, "error": f"Không tìm thấy bản lưu trữ của hộ chiếu {passport} ở nhà nào. "
                                      "Hồ sơ chạy trước 20/11/2026 hoặc chưa chạy xong: nhập thêm tên thư mục và chọn nhà."}
    if len(found) > 1:
        return {"ok": False, "error": "Hộ chiếu có bản lưu trữ ở nhiều nhà: "
                                      f"{', '.join(r['house'] for r in found)}. Chọn nhà rồi Kiểm tra lại."}
    return found[0]


def _local(house: dict[str, str], path: str) -> str:
    return f"http://127.0.0.1:{house['api_port']}{path}"


def _json_or_error(resp) -> dict[str, Any]:
    try:
        data = resp.json()
    except ValueError:
        data = {"ok": False, "error": resp.text[:300]}
    if resp.status_code >= 400:
        detail = data.get("detail", data) if isinstance(data, dict) else data
        return {"ok": False, **(detail if isinstance(detail, dict) else {"error": str(detail)})}
    return data


def folder_stat(house_name: str, source_prefix: str) -> dict[str, Any]:
    """Files already under the folder in the house's bucket (asked before uploading)."""
    house = house_config(house_name)
    resp = requests.post(_local(house, "/r2/folders/stat"), json={"prefix": normalize_source_prefix(source_prefix)}, timeout=30)
    return _json_or_error(resp)


def upload_file(house_name: str, source_prefix: str, relative_path: str, content: bytes,
                content_type: str = "") -> dict[str, Any]:
    """Put one file of the chosen folder into the house's bucket at <folder>/<relative path>."""
    house = house_config(house_name)
    folder = normalize_source_prefix(source_prefix)
    rel = str(relative_path or "").replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in rel.split("/") or rel.endswith("/"):
        raise FormError(f"Tên file không hợp lệ: {relative_path}")
    if not content:
        raise FormError(f"File rỗng: {rel}")
    resp = requests.post(
        _local(house, "/r2/images"),
        data={"mode": "upload", "key": folder + rel, "content_type": content_type},
        files={"file": (rel.rsplit("/", 1)[-1], content, content_type or "application/octet-stream")},
        timeout=180,
    )
    return _json_or_error(resp)


# Images of a case on R2, in the passport folder (= passport number). The house
# instance finds the keys (/r2/case-images): the passport image as /run picks it,
# the edited portrait saved by n8n WF-08, the CT07 (one PDF made by WF-07B) and
# the old Chinese visas (WF-09). CT07 / visa: several files (or PDF pages) are
# shown as one image, stacked.
CASE_IMAGES = {"passport": "Ảnh hộ chiếu", "portrait": "Ảnh chân dung", "ct07": "CT07", "visa": "Visa cũ",
               "moi": "qmoi_1"}
_PASSPORT_FOLDER_RE = re.compile(r"^[A-Za-z0-9_-]{3,40}$")
_STACK_WIDTH = 1400       # px, width of a stacked image
_STACK_MAX_PAGES = 8


_DATED_VISA_RE = re.compile(r"^(?:visa_cu|file)_(\d{4}-\d{2}-\d{2})_")


def pick_old_visas(keys: list[str], issue_date: str = "") -> list[str]:
    """The old visa image(s) the curl's old_* fields were read from.

    WF-09 keeps the visa with the latest issue date and puts that date in the
    file name: visa_cu_<date>_n (old passport), file_<date>_n (current passport,
    since 2026-11-25; older cases have file_<n>, no date). So: the visas of
    issue_date, else the undated ones (one of them is it), else every old visa."""
    date = re.sub(r"[^0-9-]", "", str(issue_date or ""))
    dated = [(k, _DATED_VISA_RE.match(k.rsplit("/", 1)[-1].lower())) for k in keys]
    if date:
        same = [k for k, m in dated if m and m.group(1) == date]
        if same:
            return same
    undated = [k for k, m in dated if not m]
    return undated or list(keys)


_INVITER_DOC_RE = re.compile(r"^[qs]moi_0*1(?!\d)")


def pick_inviter_doc(keys: list[str]) -> list[str]:
    """Q1 / Q2 / S2: the inviter's first paper, qmoi_1 (S2: smoi_1; every page
    when it was split), else the first qmoi_ / smoi_ file. Not smoi_ruot_ etc."""
    names = [(k, k.rsplit("/", 1)[-1].lower()) for k in keys]
    first = [k for k, n in names if _INVITER_DOC_RE.match(n)]
    if first:
        return first
    any_moi = [k for k, n in names if re.match(r"^[qs]moi_\d", n)]
    return any_moi[:1]


def _stack_pages(files: list[tuple[str, bytes]]) -> bytes:
    """One JPEG: every image / PDF page, top to bottom, same width."""
    import fitz
    from PIL import Image

    pages: list[Image.Image] = []
    for name, data in files:
        if name.lower().endswith(".pdf") or data[:4] == b"%PDF":
            with fitz.open(stream=data, filetype="pdf") as doc:
                for page in doc:
                    if len(pages) >= _STACK_MAX_PAGES:
                        break
                    zoom = _STACK_WIDTH / max(page.rect.width, 1)
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                    pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        else:
            try:
                pages.append(Image.open(BytesIO(data)).convert("RGB"))
            except Exception:
                continue
        if len(pages) >= _STACK_MAX_PAGES:
            break
    if not pages:
        raise RuntimeError("Không đọc được file ảnh / PDF")
    scaled = [p.resize((_STACK_WIDTH, max(1, round(p.height * _STACK_WIDTH / p.width)))) for p in pages]
    gap = 16
    out = Image.new("RGB", (_STACK_WIDTH, sum(p.height for p in scaled) + gap * (len(scaled) - 1)), (200, 200, 200))
    y = 0
    for p in scaled:
        out.paste(p, (0, y))
        y += p.height + gap
    buf = BytesIO()
    out.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def case_image(house_name: str, passport_number: str, kind: str,
               issue_date: str = "") -> tuple[int, bytes, str, str]:
    """(status, content, content_type, file name) of one case image from the house's bucket.

    ``issue_date``: the curl's old_issueDate, to pick the old visa (kind "visa")."""
    house = house_config(house_name)
    folder = str(passport_number or "").strip().upper()
    if not _PASSPORT_FOLDER_RE.match(folder):
        raise FormError(f"Số hộ chiếu không hợp lệ: {passport_number or '(trống)'}")
    if kind not in CASE_IMAGES:
        raise FormError(f"Loại ảnh không hợp lệ: {kind}")
    found = _json_or_error(requests.get(_local(house, "/r2/case-images"), params={"passport": folder}, timeout=60))
    if not found.get("ok"):
        raise RuntimeError(found.get("message") or found.get("error") or "Không liệt kê được thư mục R2")
    if kind == "ct07":
        keys = list(found.get("ct07") or [])
    elif kind == "visa":
        keys = pick_old_visas(list(found.get("old_visas") or []), issue_date)
    elif kind == "moi":
        keys = pick_inviter_doc(list(found.get("inviter_docs") or []))
    else:
        keys = [str(found.get(kind) or "")] if found.get(kind) else []
    if not keys:
        return 404, b"", "", ""
    if len(keys) == 1 and not keys[0].lower().endswith(".pdf"):
        key = keys[0]
        resp = requests.get(_local(house, "/r2/images/get"), params={"key": key}, timeout=60)
        ext = key.rsplit(".", 1)[-1].lower() if "." in key.rsplit("/", 1)[-1] else "png"
        name = f"{folder}_{kind}.{ext}"
        return resp.status_code, resp.content, resp.headers.get("content-type", "application/octet-stream"), name
    files = []
    for key in keys[:_STACK_MAX_PAGES]:
        resp = requests.get(_local(house, "/r2/images/get"), params={"key": key}, timeout=60)
        if resp.status_code >= 400:
            return resp.status_code, b"", "", ""
        files.append((key, resp.content))
    return 200, _stack_pages(files), "image/jpeg", f"{folder}_{kind}.jpg"


CASE_IMAGE_MAX_BYTES = 15 * 1024 * 1024
_IMAGE_CONTENT_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp",
                        "bmp": "image/bmp", "tif": "image/tiff", "tiff": "image/tiff"}


def _reencode_image(content: bytes, ext: str) -> bytes:
    """The uploaded photo re-encoded to the format of the file it replaces (the key keeps its
    extension, so OCR / COVA never get a PNG name holding JPEG bytes). FormError when not an image."""
    import cv2
    import numpy as np

    img = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FormError("File tải lên không phải ảnh (chỉ nhận .jpg, .png, .webp…)")
    target = "jpg" if ext in ("jpg", "jpeg") else ext if ext in _IMAGE_CONTENT_TYPES else "png"
    params = [int(cv2.IMWRITE_JPEG_QUALITY), 95] if target == "jpg" else []
    ok, buf = cv2.imencode("." + target, img, params)
    if not ok:
        raise FormError(f"Không chuyển được ảnh sang .{target}")
    return buf.tobytes()


def replace_case_image(house_name: str, passport_number: str, kind: str, content: bytes) -> dict[str, Any]:
    """Overwrite the passport image of a case (when the one on R2 is wrong).

    Writes over the exact key /web/case-image shows (= the image /run sends to OCR), in the same
    format; nothing there yet -> <PASSPORT>/passport.png. The next Chạy downloads the folder again
    and reads the new image. The old file is not kept."""
    house = house_config(house_name)
    folder = str(passport_number or "").strip().upper()
    if not _PASSPORT_FOLDER_RE.match(folder):
        raise FormError(f"Số hộ chiếu không hợp lệ: {passport_number or '(trống)'}")
    if kind != "passport":
        raise FormError("Chỉ thay được ảnh hộ chiếu")
    if not content:
        raise FormError("Chưa chọn ảnh")
    if len(content) > CASE_IMAGE_MAX_BYTES:
        raise FormError(f"Ảnh lớn hơn {CASE_IMAGE_MAX_BYTES // 1048576} MB")
    found = _json_or_error(requests.get(_local(house, "/r2/case-images"), params={"passport": folder}, timeout=60))
    if not found.get("ok"):
        raise RuntimeError(found.get("message") or found.get("error") or "Không liệt kê được thư mục R2")
    key = str(found.get("passport") or "") or f"{folder}/passport.png"
    name = key.rsplit("/", 1)[-1]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "png"
    data = _reencode_image(content, ext)
    content_type = _IMAGE_CONTENT_TYPES.get(ext, "image/png")
    resp = requests.post(
        _local(house, "/r2/images"),
        data={"mode": "upload", "key": key, "content_type": content_type},
        files={"file": (name, data, content_type)},
        timeout=180,
    )
    result = _json_or_error(resp)
    if not result.get("ok"):
        raise RuntimeError(result.get("message") or result.get("error") or "Tải ảnh lên R2 không được")
    return {"ok": True, "key": key, "size": len(data), "replaced": bool(found.get("passport"))}


def bio_credentials(house_name: str) -> dict[str, Any]:
    """Bio login URL + account of the house (from the house instance's own .env)."""
    house = house_config(house_name)
    return _json_or_error(requests.get(_local(house, "/bio/credentials"), timeout=15))


def bio_save_authorization(house_name: str, authorization: str) -> dict[str, Any]:
    """Check the token and store it in the house's token file (used by /run)."""
    house = house_config(house_name)
    return _json_or_error(requests.post(_local(house, "/bio/authorization"),
                                        json={"authorization": authorization}, timeout=60))


def bio_current_authorization(house_name: str) -> dict[str, Any]:
    """The token the house uses now (its token file)."""
    house = house_config(house_name)
    return _json_or_error(requests.get(_local(house, "/bio/authorization/current"), timeout=15))


def bio_check_authorization(house_name: str) -> dict[str, Any]:
    """Is the token the house has now still accepted?"""
    house = house_config(house_name)
    return _json_or_error(requests.get(_local(house, "/bio/authorization/check"), timeout=60))


def house_by_port(port: Any) -> str:
    for name, cfg in HOUSES.items():
        if str(port).strip() == cfg["api_port"]:
            return name
    raise FormError(f"Cổng {port} không thuộc nhà nào (chỉ nhận {', '.join(c['api_port'] for c in HOUSES.values())})")


def run_case(house_name: str, body: Any) -> dict[str, Any]:
    """Run the (edited) curl body on /run of the house's instance - like sending it from Postman.
    Only the port of the pasted curl is used; the host is always 127.0.0.1."""
    house = house_config(house_name)
    if not isinstance(body, dict) or not body:
        raise FormError("Nội dung JSON của curl rỗng hoặc không phải object")
    resp = requests.post(_local(house, "/run"), json=body, timeout=1800)
    try:
        data = resp.json()
    except ValueError:
        data = {"raw": resp.text[:5000]}
    return {"ok": resp.status_code < 400, "status_code": resp.status_code, "house": house["house"], "response": data}


_NAME_KEYS = ("full_name", "fullName", "fullname", "name_en")


def _find_name(data: Any, depth: int = 0) -> str:
    if depth > 3:
        return ""
    if isinstance(data, dict):
        for k in _NAME_KEYS:
            if isinstance(data.get(k), str) and data[k].strip():
                return data[k].strip()
        for v in data.values():
            found = _find_name(v, depth + 1)
            if found:
                return found
    return ""


def history_entry(user: dict[str, Any], result: dict[str, Any], port: Any, body: dict[str, Any], seconds: float) -> dict[str, Any]:
    """What the curl history keeps of a successful run. The token is dropped: reusing the curl
    later takes the house's current token (authorization "")."""
    house = house_config(result["house"])
    clean = {**body}
    if "authorization" in clean:
        clean["authorization"] = ""
    return {
        "username": user["username"],
        "staff_code": user.get("staff_code", ""),
        "house": house["house"],
        "port": str(port or house["api_port"]),
        "passport_number": str(body.get("passportNumber") or "").strip(),
        "full_name": _find_name(result.get("response")),
        "visa_type": str(body.get("visa_type") or "").strip(),
        "body": clean,
        "seconds": seconds,
    }


# Progress steps n8n reports (POST /web/progress) - shown in this order on the page.
STEPS = [
    ("received", "Đã nhận hồ sơ"),
    ("files_loaded", "Đã tải file"),
    ("classifying", "Đang phân loại tài liệu"),
    ("processing", "Đang xử lý giấy tờ"),
    ("building", "Đang dựng hồ sơ"),
    ("done", "Xong: curl đã gửi Telegram"),
]
_STEP_LABELS = dict(STEPS) | {"error": "Lỗi"}


def make_step(step: str, message: str = "", at: str = "") -> dict[str, str]:
    key = str(step or "").strip()
    if key not in _STEP_LABELS:
        raise FormError(f"Bước không hợp lệ: {key}")
    return {"step": key, "label": _STEP_LABELS[key], "message": str(message or "")[:1500], "at": at}


def step_status(step: str) -> str:
    return "done" if step == "done" else "error" if step == "error" else "running"


def form_options() -> dict[str, Any]:
    return {
        "houses": list(HOUSES),
        "visa_codes": VISA_CODES,
        "relations": RELATIONS,
        "relation_required": sorted(_RELATION_REQUIRED),
        "phone_required": sorted(PHONE_REQUIRED),
        "steps": [{"step": k, "label": v} for k, v in STEPS],
    }
