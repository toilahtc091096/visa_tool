from docxtpl import DocxTemplate
from datetime import date, timedelta
from pathlib import Path
from docx2pdf import convert
from typing import Any
import re


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

    base = (
        Path(__file__).resolve().parent / ".." / "resources"
    )  # folder relative to this .py
    src = (base / file_name).resolve()
    out_dir = (base / output_path).resolve()  # ./output next to this .py
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
        }
    )

    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert(str(out), str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX
