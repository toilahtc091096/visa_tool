from docxtpl import DocxTemplate
from datetime import date, timedelta
from pathlib import Path

import asyncio

async def render_docx_template(file_name: str,names: list[str], first: date, end: date | None = None) -> str:
    """
    Render a DOCX template with docxtpl asynchronously.

    Args:
        file_name: Path to input .docx template
        first: Value for template variable {{ first }}
        output_file: Path to save output. If None, appends _done before .docx

    Returns:
        Path to saved output file
    """
    base = Path(__file__).resolve().parent / ".." / "test"   # folder relative to this .py
    src = (base / file_name).resolve()
    out_dir = (base / "output").resolve()      # ./output next to this .py
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Docx not found: {src}")

    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")

    out = out_dir / (Path(file_name).stem + "_done.docx")
    doc = DocxTemplate(str(src))
    second_first = (first + timedelta(weeks=1));
    second_end = (end + timedelta(weeks=1));
    third_first = (first + timedelta(weeks=2));
    third_end = (end + timedelta(weeks=2));
    cancel_day_free = (first - timedelta(days=2));
    cancel_day_lost_free = (first - timedelta(days=1));
    doc.render({
        "first": first.day, 
        "f_month_num": first.month, 
        "f_month_text": first.strftime("%B").upper(),
        "end": end.day, 
        "e_month_num": end.month,
        "e_month_text": end.strftime("%B").upper(),
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
        "cancel_day_free_d":cancel_day_free.day,
        "cancel_day_free_m":cancel_day_free.month,
        "cancel_day_free_y":cancel_day_free.year,
        "cancel_day_free_month_text": cancel_day_free.strftime("%B").upper(),
        "cancel_day_lost_fee_d":cancel_day_lost_free.day,
        "cancel_day_lost_fee_m":cancel_day_lost_free.month,
        "cancel_day_lost_fee_y":cancel_day_lost_free.year,
        "cancel_day_lost_fee_month_text": cancel_day_lost_free.strftime("%B").upper(),
        "name_list": names
        })   
    doc.save(str(out))
    return out


# Example usage:
# asyncio.run(render_docx_template("../test/L30_Khach_san.docx", "6",
#                                 "../test/output/L30_Khach_san_done.docx"))