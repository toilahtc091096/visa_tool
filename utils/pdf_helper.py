import os
import tempfile
import uuid
from pathlib import Path

from env_loader import load_dotenv

load_dotenv()

_DEFAULT_DLL_DIRS = [
    r"C:\msys64\mingw64\bin",
    r"C:\msys64\ucrt64\bin",
]


def _configure_weasyprint_dll_search_path() -> None:
    dll_dirs_raw = os.environ.get("WEASYPRINT_DLL_DIRECTORIES", "")
    dll_dirs = [
        directory.strip()
        for directory in dll_dirs_raw.split(";")
        if directory.strip()
    ]
    if not dll_dirs:
        dll_dirs = [directory for directory in _DEFAULT_DLL_DIRS if Path(directory).exists()]
        if dll_dirs:
            os.environ["WEASYPRINT_DLL_DIRECTORIES"] = ";".join(dll_dirs)

    path_value = os.environ.get("PATH", "")
    path_parts = path_value.split(os.pathsep) if path_value else []
    for directory in reversed(dll_dirs):
        if directory and directory not in path_parts:
            path_parts.insert(0, directory)
    if path_parts:
        os.environ["PATH"] = os.pathsep.join(path_parts)

    if os.name == "nt":
        for directory in dll_dirs:
            if Path(directory).exists():
                os.add_dll_directory(directory)


_configure_weasyprint_dll_search_path()

from weasyprint import HTML


def convert_html_to_pdf(html_content: bytes) -> str:
    html_text = html_content.decode("utf-8", errors="replace")
    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(tempfile.gettempdir(), pdf_filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        html_path = Path(tmp_dir) / "input.html"
        html_path.write_text(html_text, encoding="utf-8")
        HTML(filename=str(html_path), base_url=tmp_dir).write_pdf(pdf_path)

    return pdf_path


from pypdf import PdfReader, PdfWriter

def remove_last_blank_page(pdf_path: str):
    reader = PdfReader(pdf_path)

    if len(reader.pages) <= 1:
        return

    writer = PdfWriter()

    # giữ tất cả trang trừ trang cuối
    for page in reader.pages[:-1]:
        writer.add_page(page)

    with open(pdf_path, "wb") as f:
        writer.write(f)