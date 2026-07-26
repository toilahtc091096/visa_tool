from os import name

from docxtpl import DocxTemplate
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re
from generate_file.docx_to_pdf import convert_docx_to_pdf
from generate_file.path_utils import passport_data_dir


def _normalize_passengers(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(
                {
                    "name": item.get("name", ""),
                    "sex": item.get("sex", ""),
                    "nationality": item.get("nationality", ""),
                    "passportNo": item.get("passportNo", ""),
                    "birth_date_dd_mm_yyyy": item.get(
                        "birth_date_dd_mm_yyyy", ""
                    ),
                    "expired_day_dd_mm_yyyy": item.get(
                        "expired_day_dd_mm_yyyy", ""
                    ),
                }
            )
    return result


async def render_docx_template_output_pdf(
    payload: dict[str, Any],
    output_path: str = "",
    passport_number: str = "",
) -> str:
    """
    Render a DOCX template with docxtpl asynchronously.

    Args:
        file_name: Path to input .docx template
        first: Value for template variable {{ first }}
        output_file: Path to save output. If None, appends _done before .docx

    Returns:
        Path to saved output file
    """
    file_name: str = payload.get("file_name")
    name: str = payload.get("names", "")
    extra_passengers = _normalize_passengers(payload.get("passengers", []))

    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = passport_data_dir(passport_number)
    src = (templates_base / file_name).resolve()
    out_dir = (output_base / output_path).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Docx not found: {src}")

    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")
    if isinstance(name, list):
        name = "_".join(name)
    entry_type = payload.get("entry_type", "");
    entry_type_show = "1";
    if entry_type == "S":
        entry_type_show = "1";
    elif entry_type == "D":
        entry_type_show = "2";
    elif entry_type == "M":
        entry_type_show = "多";
        
    name = f"{name}_{entry_type}"
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")

    out = out_dir / (Path(file_name).stem + ".docx")
    doc = DocxTemplate(str(src))
    doc.render(
        {
            "passengers": [
                {
                    "name": name,
                    "sex": payload.get("sex"),
                    "nationality": payload.get("nationality"),
                    "passportNo": payload.get("passportNo"),
                    "birth_date_dd_mm_yyyy": payload.get("birth_date_dd_mm_yyyy"),
                    "expired_day_dd_mm_yyyy": payload.get("expired_day_dd_mm_yyyy"),
                },
                *extra_passengers,
            ],
            "visa_type_first": payload.get("visa_type_first"),
            "visa_type_number": payload.get("visa_type_number"),
            "submit_year_yyyy": payload.get("submit_year_yyyy"),
            "submit_month_mm": payload.get("submit_month_mm"),
            "submit_day_dd": payload.get("submit_day_dd"),
            "entry_type_show": entry_type_show,
        }
    )

    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX
