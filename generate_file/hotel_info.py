from docxtpl import DocxTemplate
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import re
from jinja2 import Environment
from utils import vnd, cny, vnd_decimal, date_util
from constants import UNIT_OF_HOTEL, VIETNAMESE_NAMES, L_30_HOTEL_INFO
import random
from generate_file.docx_to_pdf import convert_docx_to_pdf
from pathlib import Path
from PyPDF2 import PdfMerger
from docx2pdf import convert

from utils import pdf_helper

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
    is_under_18: bool = payload.get("is_under_18", False)
    haveChildFlag: bool = payload.get("haveChildFlag", False)

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
                "unit_of_hotel": int(UNIT_OF_HOTEL) + random.randint(10000, 50000),
                # xet lai, truong hop nay < 18 tuoi, nen lam rieng, 2 bien nay nen chuyen tu main
                "adults_number": 1,
                "child_number": 1,
                # end
                "three_submit_number": (
                    random.randint(100, 999)
                    if not (is_under_18 and haveChildFlag)
                    else "231"
                ),
            },
            jinja_env=jinja_env,
        )
    doc.save(str(out))
    safe = safe or "NONAME"

    pdf_out = out.with_name(f"{out.stem}_{safe}.pdf")

    convert_docx_to_pdf(str(out), str(pdf_out))
    out.unlink()  # same as os.remove(out)
    return str(pdf_out)  # return PDF, not DOCX


async def render_L30_hotel(payload: dict[str, Any], output_path: str = "") -> str:
    """
    Render a DOCX template with docxtpl asynchronously.

    Args:
        file_name: Path to input .docx template
        first: Value for template variable {{ first }}
        output_file: Path to save output. If None, appends _done before .docx

    Returns:
        Path to saved output file
    """
    names: list[str] = payload.get("names", [])

    while len(names) < 4:
        name = random.choice(VIETNAMESE_NAMES).upper()
        if name not in names:
            names.append(name)
    first: date = payload.get("first")

    stays = date_util.build_three_stays(first)

    is_under_18: bool = payload.get("is_under_18", False)
    haveChildFlag: bool = payload.get("haveChildFlag", False)

    templates_base = Path(__file__).resolve().parent / ".." / "resources"
    output_base = Path(__file__).resolve().parent / ".." / "resources/data"
    srcs = []
    for i, hotel in enumerate(L_30_HOTEL_INFO):
        srcs.append(templates_base / hotel.get("documentName"))
    out_dir = (output_base / output_path).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for src in srcs:
        src = (templates_base / src).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Docx not found: {src}")

    if src.suffix.lower() != ".docx":
        raise ValueError(f"Not a .docx file: {src}")
    name_part = "_".join(names)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name_part).strip("_")
    outs = []
    for src in srcs:
        outs.append(out_dir / (Path(src).stem + ".docx"))
    jinja_env = Environment(autoescape=True)
    jinja_env.filters["vnd"] = vnd
    jinja_env.filters["cny"] = cny
    jinja_env.filters["vnd_decimal"] = vnd_decimal
    if payload.get("type") == "hotel":
        for i, src in enumerate(srcs):
            doc = DocxTemplate(str(src))
            first: date | None = date.fromisoformat(stays[i]["arrivalDate"])
            end: date | None = date.fromisoformat(stays[i]["leaveDate"])
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
                    "names": names,
                    "unit_of_hotel": UNIT_OF_HOTEL + random.randint(10000, 100000),
                    "three_submit_number": (
                        random.randint(100, 999)
                        if not (is_under_18 and haveChildFlag)
                        else 231
                    ),
                },
                jinja_env=jinja_env,
            )
            doc.save(str(outs[i]))
            safe = safe or "NONAME"

    pdf_out = merge_docx_files(
        out_dir,
        [o.name for o in outs],
        f"merged_{safe}.pdf",
    )
    for o in outs:
        if o.exists():
            o.unlink()
    return str(pdf_out)


def merge_docx_files(
    folder_path: str,
    file_names: list[str],
    output_name: str = "merged.pdf",
) -> str:
    """
    Convert từng DOCX sang PDF rồi merge PDF.
    Giữ nguyên header/footer của từng file.
    """

    if len(file_names) != 3:
        raise ValueError("file_names must contain exactly 3 file names in order")

    folder = Path(folder_path)

    docx_paths = [folder / name for name in file_names]

    missing = [str(p) for p in docx_paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing file(s): {missing}")

    pdf_paths: list[Path] = []

    # convert từng file
    for docx_path in docx_paths:
        pdf_path = docx_path.with_suffix(".pdf")

        convert(str(docx_path), str(pdf_path))
        pdf_helper.remove_last_blank_page(str(pdf_path))

        pdf_paths.append(pdf_path)

    merger = PdfMerger()

    try:
        for pdf_path in pdf_paths:
            merger.append(str(pdf_path))

        out_path = folder / output_name
        merger.write(str(out_path))
    finally:
        merger.close()
        # Xóa DOCX gốc
        for p in docx_paths:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        # Xóa PDF tạm
        for p in pdf_paths:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
    return str(out_path)
