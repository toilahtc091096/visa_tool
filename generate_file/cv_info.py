from docxtpl import DocxTemplate
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re
from generate_file.docx_to_pdf import convert_docx_to_pdf


async def render_docx_template_output_pdf(
    payload: dict[str, Any], output_path: str = ""
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
    names: list[str] = payload.get("names", [])
    output_folder: str = payload.get("passportNumber")

    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = Path(__file__).resolve().parent / ".." / "resources/data"
    src = (templates_base / file_name).resolve()
    out_dir = (output_base / output_path).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Docx not found: {src}")

    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")
    name_part = "_".join(names)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name_part).strip("_")

    out = out_dir / (Path(file_name).stem + ".docx")
    doc = DocxTemplate(str(src))
    doc.render(
        {
            "names": names,
            "visa_type_first": payload.get("visa_type_first"),
            "visa_type_number": payload.get("visa_type_number"),
            "submit_year_yyyy": payload.get("submit_year_yyyy"),
            "submit_month_mm": payload.get("submit_month_mm"),
            "submit_day_dd": payload.get("submit_day_dd"),
            "sex": payload.get("sex"),
            "nationality": payload.get("nationality"),
            "passportNo": payload.get("passportNo"),
            "birth_date_dd_mm_yyyy": payload.get("birth_date_dd_mm_yyyy"),
            "expired_day_dd_mm_yyyy": payload.get("expired_day_dd_mm_yyyy"),
        }
    )

    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX
