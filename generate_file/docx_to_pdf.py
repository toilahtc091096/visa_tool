from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path


_WORD_AUTOMATION_LOCK = threading.Lock()


@contextmanager
def _initialized_com():
    """Initialize COM in the *current* thread and balance that initialization."""
    import pythoncom

    initialized_here = False
    try:
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        initialized_here = True
    except pythoncom.com_error as exc:
        # RPC_E_CHANGED_MODE means the caller already initialized this thread
        # with another apartment model. COM is usable; it must not be
        # uninitialized by us because we do not own that initialization.
        hresult = getattr(exc, "hresult", exc.args[0] if exc.args else None)
        rpc_e_changed_mode = getattr(pythoncom, "RPC_E_CHANGED_MODE", -2147417850)
        if hresult != rpc_e_changed_mode:
            raise

    try:
        yield
    finally:
        if initialized_here:
            pythoncom.CoUninitialize()


def _convert_with_word(source: Path, target: Path) -> None:
    """
    Convert in the calling thread with an explicitly owned Word COM instance.

    Keeping COM initialization, DispatchEx, document access and cleanup in the
    same thread is essential when this function is called from an ASGI worker
    thread. Word automation is also serialized because concurrent Word COM
    operations in one worker process are unreliable.
    """
    with _WORD_AUTOMATION_LOCK, _initialized_com():
        import pythoncom
        import win32com.client

        word = None
        document = None
        try:
            # DispatchEx avoids attaching a request to an interactive or stale
            # Word instance left behind by another process/request.
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            document = word.Documents.Open(
                str(source),
                ConfirmConversions=False,
                ReadOnly=True,
                AddToRecentFiles=False,
            )
            # 17 == wdExportFormatPDF. ExportAsFixedFormat is more reliable
            # than SaveAs for PDF and does not change the source document.
            document.ExportAsFixedFormat(str(target), 17)
        except pythoncom.com_error as exc:
            raise RuntimeError(
                f"Microsoft Word could not convert '{source}' to PDF: {exc}"
            ) from exc
        finally:
            if document is not None:
                try:
                    document.Close(False)
                except pythoncom.com_error:
                    pass
                finally:
                    document = None
            if word is not None:
                try:
                    word.Quit()
                except pythoncom.com_error:
                    pass
                finally:
                    word = None


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """
    Convert a DOCX file to PDF.

    On Windows, use Microsoft Word through COM.
    On Linux and macOS, use LibreOffice headless via `soffice`.
    """
    source = Path(docx_path).resolve()
    target = Path(pdf_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"DOCX source file does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        _convert_with_word(source, target)
        if not target.is_file():
            raise RuntimeError(
                f"Microsoft Word finished without creating the PDF: {target}"
            )
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
