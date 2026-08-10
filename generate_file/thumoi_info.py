from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any
import re

from docxtpl import DocxTemplate

from generate_file.docx_to_pdf import convert_docx_to_pdf
from generate_file.path_utils import passport_data_dir
from utils import pdf_helper
SIGNATURE_MEDIA_NAME = "Image 1"


CHECKED = "☑"
UNCHECKED = "□"


def _get_value(source: Any, *keys: str, default: Any = "") -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        for key in keys:
            if key in source and source[key] not in (None, ""):
                return source[key]
        return default
    for key in keys:
        value = getattr(source, key, None)
        if value not in (None, ""):
            return value
    return default


def _text(value: Any) -> str:
    return str(value or "").strip()


def _checkbox(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on", "☑", "x"}:
            return CHECKED
        if text in {"0", "false", "no", "n", "off", "□"}:
            return UNCHECKED
    return CHECKED if bool(value) else UNCHECKED


def _split_birthday(value: Any) -> tuple[str, str, str]:
    text = _text(value)
    if not text:
        return "", "", ""
    if isinstance(value, date):
        return f"{value.year:04d}", f"{value.month:02d}", f"{value.day:02d}"
    match = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$", text)
    if match:
        return match.group(1), match.group(2), match.group(3)
    match = re.match(r"^\s*(\d{4})/(\d{2})/(\d{2})\s*$", text)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return "", "", ""


def _today_parts(source: Any) -> tuple[str, str, str]:
    register_date = _get_value(source, "register_date", default=None)
    if isinstance(register_date, date):
        return (
            f"{register_date.year:04d}",
            f"{register_date.month:02d}",
            f"{register_date.day:02d}",
        )
    if isinstance(register_date, str) and register_date.strip():
        year, month, day = _split_birthday(register_date)
        if year:
            return year, month, day
    today = date.today()
    return f"{today.year:04d}", f"{today.month:02d}", f"{today.day:02d}"


def _normalize_relation_label(value: str) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip().lower()


def _resolve_relation_flags(source: Any) -> dict[str, str]:
    explicit_flags = {
        "spouse": _get_value(source, "spouse", default=None),
        "parents": _get_value(source, "parents", default=None),
        "spouseParents": _get_value(source, "spouseParents", default=None),
        "children": _get_value(
            source, "childrenCheckbox", "childrenFlag", "children_relation", default=None
        ),
        "siblings": _get_value(source, "siblings", default=None),
        "paternalGrandparents": _get_value(
            source, "paternalGrandparents", default=None
        ),
        "maternalGrandparents": _get_value(
            source, "maternalGrandparents", default=None
        ),
        "grandchildren": _get_value(source, "grandchildren", default=None),
        "maternalGrandchildren": _get_value(
            source, "maternalGrandchildren", default=None
        ),
        "childrenSpouse": _get_value(source, "childrenSpouse", default=None),
        "relative": _get_value(source, "relative", default=None),
        "relativeNote": _get_value(source, "relativeNote", default=""),
    }

    relation_hint = _normalize_relation_label(
        _get_value(
            source,
            "inviterRelation",
            "inviter_relation",
            "relativeType",
            "relative_type",
            "relationType",
            "relation_type",
            default="",
        )
    )

    if explicit_flags["spouse"] is None and relation_hint in {
        "spouse",
        "vo chong",
        "vợ chồng",
        "husband",
        "wife",
        "chong",
        "vo",
    }:
        explicit_flags["spouse"] = CHECKED
    if explicit_flags["parents"] is None and relation_hint in {
        "parents",
        "bo me",
        "ba me",
        "father",
        "mother",
    }:
        explicit_flags["parents"] = CHECKED
    if explicit_flags["siblings"] is None and relation_hint in {
        "siblings",
        "brother",
        "sister",
        "anh em",
    }:
        explicit_flags["siblings"] = CHECKED
    if explicit_flags["children"] is None and relation_hint in {
        "children",
        "child",
        "son",
        "daughter",
    }:
        explicit_flags["children"] = CHECKED

    if explicit_flags["relative"] is None:
        explicit_flags["relative"] = CHECKED if relation_hint else UNCHECKED
    if not _text(explicit_flags["relativeNote"]) and relation_hint:
        explicit_flags["relativeNote"] = _text(
            _get_value(source, "inviterRelation", "relativeNote", default="")
        )

    normalized_flags = {
        key: _checkbox(value)
        for key, value in explicit_flags.items()
        if key != "relativeNote"
    }
    normalized_flags["relativeNote"] = _text(explicit_flags["relativeNote"])
    return normalized_flags


def build_thumoi_context(source: Any) -> dict[str, Any]:
    inviter_family = _text(
        _get_value(source, "inviterFamilyName", "inviter_family_name", default="")
    )
    inviter_given = _text(
        _get_value(source, "inviterGivenName", "inviter_given_name", default="")
    )
    inviter_name = _text(
        _get_value(source, "inviterName", "inviter_name", default="")
    ) or f"{inviter_family}{inviter_given}"

    passport_number = _text(
        _get_value(source, "passportNumber", "passport_number", default="")
    )
    applicant_name = _text(_get_value(source, "name", default=""))
    if not applicant_name:
        family = _text(_get_value(source, "familyName", "family_name", default=""))
        given = _text(_get_value(source, "firstName", "first_name", default=""))
        applicant_name = " ".join(part for part in [family, given] if part).strip()

    birthday_year, birthday_month, birthday_day = _split_birthday(
        _get_value(source, "birthday", "birth_date", default="")
    )
    today_year, today_month, today_day = _today_parts(source)
    relation_flags = _resolve_relation_flags(source)

    visa_type = _text(_get_value(source, "visa_type", "visaType", default="")).upper()
    visa_duration = _text(
        _get_value(source, "visa_duration", "apply_visa_validity", default="")
    ).upper()

    q1 = _get_value(source, "q1", default=None)
    q2_once = _get_value(source, "q2Once", "q2_once", default=None)
    q2_twice = _get_value(source, "q2Twice", "q2_twice", default=None)
    q2_half_year = _get_value(source, "q2HalfYear", "q2_half_year", default=None)
    q2_one_year = _get_value(source, "q2OneYear", "q2_one_year", default=None)
    if q1 is None and visa_type == "Q1":
        q1 = CHECKED
    if q2_once is None and visa_type == "Q2" and visa_duration in {"1", "ONCE"}:
        q2_once = CHECKED
    if q2_twice is None and visa_type == "Q2" and visa_duration in {"2", "TWICE"}:
        q2_twice = CHECKED
    if (
        q2_half_year is None
        and visa_type == "Q2"
        and visa_duration in {"6", "HALFYEAR", "HALF_YEAR", "180"}
    ):
        q2_half_year = CHECKED
    if (
        q2_one_year is None
        and visa_type == "Q2"
        and visa_duration in {"12", "1Y", "ONEYEAR", "ONE_YEAR", "365"}
    ):
        q2_one_year = CHECKED

    return {
        "inviterName": inviter_name,
        "inviterIdCard": _text(
            _get_value(source, "inviterIdCard", "inviter_id_card", default="")
        ),
        "inviterPhone": _text(
            _get_value(
                source,
                "inviterPhone",
                "inviter_id_phone",
                "inviterPhone",
                "phone",
                "payMobile",
                "supervisor_mobile",
                "companyPhone",
                default="",
            )
        ),
        "inviterAddress": _text(
            _get_value(source, "inviterAddress", "inviter_address", default="")
        ),
        **relation_flags,
        "q1": _checkbox(q1),
        "q2Once": _checkbox(q2_once),
        "q2Twice": _checkbox(q2_twice),
        "q2HalfYear": _checkbox(q2_half_year),
        "q2OneYear": _checkbox(q2_one_year),
        "name": applicant_name,
        "passport_number": passport_number,
        "birth_year": birthday_year,
        "birth_month": birthday_month,
        "birth_day": birthday_day,
        "phone": _text(_get_value(source, "phone", "payMobile", default="")),
        "today_year": today_year,
        "today_month": today_month,
        "today_day": today_day,
        "signature_image_path": _text(
            _get_value(
                source,
                "signature_image_path",
                "signatureImagePath",
                default="",
            )
        ),
    }


async def render_thumoi_docx_output_pdf(
    source: Any,
    output_path: str = "tham-than/thumoi",
    passport_number: str = "",
    template_name: str = "Q_Template.docx",
) -> str:
    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = passport_data_dir(passport_number)

    src = (templates_base / template_name).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Docx not found: {src}")
    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")

    out_dir = (output_base / output_path).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    context = build_thumoi_context(source)
    signature_image_path = _text(context.pop("signature_image_path", ""))
    safe_name = re.sub(
        r"[^A-Za-z0-9_\-\u4e00-\u9fff]+",
        "_",
        f"{context.get('inviterName', '')}_{context.get('name', '')}",
    ).strip("_")
    safe_name = safe_name or "THUMOI"

    out = out_dir / (Path(template_name).stem + ".docx")
    doc = DocxTemplate(str(src))
    if signature_image_path:
        signature_path = Path(signature_image_path)
        if signature_path.is_file():
            doc.replace_pic(
                SIGNATURE_MEDIA_NAME,
                BytesIO(signature_path.read_bytes()),
            )
    doc.render(context)
    if out.exists():
        out.unlink()
    doc.save(str(out))

    pdf_out = out.with_name(f"{out.stem}_{safe_name}.pdf")
    convert_docx_to_pdf(str(out), str(pdf_out))
    pdf_helper.remove_last_blank_page(str(pdf_out))
    out.unlink(missing_ok=True)
    return str(pdf_out)
