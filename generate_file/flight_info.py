from docxtpl import DocxTemplate
import asyncio
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re
from constants import UNIT_OF_HOTEL
from utils import pdf_helper
from utils import date_util
import random
from generate_file.docx_to_pdf import convert_docx_to_pdf

async def render_flight_ticket_output_pdf(
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
    first: date = payload.get("first")
    end: date | None = payload.get("end")
    visa_type: str = payload.get("visa_type")
    if visa_type == "L30":
        stays = date_util.build_three_stays(first)
        end: date | None = date.fromisoformat(stays[-1]["leaveDate"])
    
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
    if payload.get("type") == "flight_ticket":
        first: date = payload.get("first")
        end: date | None = payload.get("end")
        if visa_type == "L30":
            end = date_util.get_end_date(first, "2W6D")
        names: list[str] = payload.get("names", [])
        doc.render(
            {
                "arrive_day": first.day,
                "arrive_month_MMM": first.strftime("%b").upper(),
                "arrive_year_yyyy": first.year,
                "departure_day": end.day,
                "departure_month_MMM": end.strftime("%b").upper(),
                "departure_year_yyyy": end.year,
                "arrvied_city": str(payload.get("arrvied_city")).upper(),
                "names": names,
                "arrive_day_name": first.strftime("%A").upper(),
                "arrive_flight_number": payload.get("arrive_flight_number"),
                "arrived_iata_code": str(payload.get("arrived_iata_code")).upper(),
                "departure_day_name": end.strftime("%A").upper(),
                "departure_flight_number": payload.get("departure_flight_number"),
                "departure_iata_code": str(payload.get("departure_iata_code")),
                "departure_city": str(payload.get("departure_city")),
            },
        )
    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    pdf_helper.remove_last_blank_page(str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX