from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """
    Convert a DOCX file to PDF.

    On Windows, use Microsoft Word through `docx2pdf`.
    On Linux and macOS, use LibreOffice headless via `soffice`.
    """
    source = Path(docx_path).resolve()
    target = Path(pdf_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        from docx2pdf import convert as docx2pdf_convert

        docx2pdf_convert(str(source), str(target))
        return

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            "LibreOffice is required to convert DOCX to PDF on non-Windows platforms."
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        command = [
            soffice,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmp_dir_path),
            str(source),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "LibreOffice failed to convert DOCX to PDF.\n"
                f"stdout:\n{exc.stdout}\n"
                f"stderr:\n{exc.stderr}"
            ) from exc

        generated_pdf = tmp_dir_path / f"{source.stem}.pdf"
        if not generated_pdf.exists():
            raise RuntimeError(
                f"LibreOffice conversion finished but did not create {generated_pdf.name}"
            )

        shutil.move(str(generated_pdf), str(target))
