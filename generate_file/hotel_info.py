from docxtpl import DocxTemplate
import asyncio
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re
from jinja2 import Environment
from utils import vnd, cny, vnd_decimal
from constants import UNIT_OF_HOTEL
import random
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
    first: date = payload.get("first")
    end: date | None = payload.get("end")

    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = Path(__file__).resolve().parent / ".." / "data"
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
    jinja_env = Environment(autoescape=True)
    jinja_env.filters["vnd"] = vnd
    jinja_env.filters["cny"] = cny
    jinja_env.filters["vnd_decimal"] = vnd_decimal
    if payload.get("type") == "hotel":
        second_first = first + timedelta(weeks=1)
        second_end = end + timedelta(weeks=1)
        third_first = first + timedelta(weeks=2)
        third_end = end + timedelta(weeks=2)
        cancel_day_free = first - timedelta(days=2)
        cancel_day_lost_free = first - timedelta(days=1)
        print(file_name)
        doc.render(
            {
                "first": first.day,
                "f_month_num": first.month,
                "f_month_text": first.strftime("%B").upper(),
                "f_day_name": first.strftime("%A").upper(),
                "end": end.day,
                "e_month_num": end.month,
                "e_month_text": end.strftime("%B").upper(),
                "e_day_name": end.strftime("%A").upper(),
                "second_first": second_first.day,
                "s_f_month_num": second_first.month,
                "s_f_month_text": second_first.strftime("%B").upper(),
                "second_end": second_end.day,
                "s_e_month_num": second_end.month,
                "s_e_month_text": second_end.strftime("%B").upper(),
                "third_first": third_first.day,
                "t_f_month_num": third_first.month,
                "t_f_month_text": third_first.strftime("%B").upper(),
                "third_end": third_end.day,
                "t_e_month_num": third_end.month,
                "t_e_month_text": third_end.strftime("%B").upper(),
                "cancel_day_free_d": cancel_day_free.day,
                "cancel_day_free_m": cancel_day_free.month,
                "cancel_day_free_y": cancel_day_free.year,
                "cancel_day_free_month_text": cancel_day_free.strftime("%B").upper(),
                "cancel_day_lost_fee_d": cancel_day_lost_free.day,
                "cancel_day_lost_fee_m": cancel_day_lost_free.month,
                "cancel_day_lost_fee_y": cancel_day_lost_free.year,
                "cancel_day_lost_fee_month_text": cancel_day_lost_free.strftime(
                    "%B"
                ).upper(),
                "names": names,
                "unit_of_hotel": UNIT_OF_HOTEL,
                # xet lai, truong hop nay < 18 tuoi, nen lam rieng, 2 bien nay nen chuyen tu main
                "adults_number": 1,
                "child_number": 1,
                # end
                "three_submit_number": random.randint(100,999)
            },
            jinja_env=jinja_env,
        )
    if payload.get("type") == "flight_ticket":
        first: date = payload.get("first")
        end: date | None = payload.get("end")
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
            jinja_env=jinja_env,
        )
    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX
 
