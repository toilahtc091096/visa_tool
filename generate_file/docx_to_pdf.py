from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path


_WORD_AUTOMATION_LOCK = threading.Lock()
_WORD_AUTOMATION_MUTEX_NAME = "Local\\visa_tool_word_automation_mutex"


@contextmanager
def _word_automation_process_lock():
    """
    Serialize Word automation across all Python processes on this machine.

    This prevents two app instances on different ports from opening Word at the
    same time, which can trigger intermittent COM initialization failures.
    """

    from ctypes import windll

    handle = windll.kernel32.CreateMutexW(None, False, _WORD_AUTOMATION_MUTEX_NAME)
    if not handle:
        raise OSError("Failed to create Word automation mutex")

    wait_result = windll.kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
    if wait_result not in (0x00000000, 0x00000080):
        windll.kernel32.CloseHandle(handle)
        raise OSError(f"Failed to acquire Word automation mutex: {wait_result}")

    try:
        yield
    finally:
        try:
            windll.kernel32.ReleaseMutex(handle)
        finally:
            windll.kernel32.CloseHandle(handle)


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


def _convert_with_word_in_fresh_thread(source: Path, target: Path) -> None:
    """
    Run Word automation on a brand-new thread so COM state from worker pools
    cannot leak into the conversion.

    This avoids the common case where a reused ASGI/threadpool worker has a
    conflicting apartment model and causes CoInitialize/CoInitializeEx errors.
    """

    error: list[BaseException] = []

    def _runner() -> None:
        try:
            _convert_with_word(source, target)
        except BaseException as exc:  # noqa: BLE001 - re-raise in caller thread
            error.append(exc)

    thread = threading.Thread(
        target=_runner,
        name="word-docx-to-pdf",
        daemon=True,
    )
    thread.start()
    thread.join()

    if error:
        raise error[0]


def _is_transient_word_com_error(exc: BaseException) -> bool:
    """
    Return True for COM failures that are often recoverable by retrying.

    We keep the check broad but conservative so we only retry likely transient
    cases such as COM apartment mismatches or Word being busy.
    """

    text = " ".join(
        part for part in [exc.__class__.__name__, str(exc)] if part
    ).lower()
    transient_markers = (
        "coinitialize",
        "coinitializeex",
        "coinit",
        "rpc_e_changed_mode",
        "rpc_e_servercall_retrylater",
        "servercall",
        "call was rejected by callee",
        "word.application",
        "com_error",
    )
    return any(marker in text for marker in transient_markers)


def _convert_with_word_with_retry(
    source: Path,
    target: Path,
    *,
    attempts: int = 2,
    delay_seconds: float = 0.75,
) -> None:
    last_error: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            _convert_with_word_in_fresh_thread(source, target)
            return
        except BaseException as exc:  # noqa: BLE001 - retry wrapper
            last_error = exc
            if attempt >= attempts or not _is_transient_word_com_error(exc):
                raise
            time.sleep(delay_seconds * attempt)

    if last_error is not None:
        raise last_error


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
    if target.exists():
        target.unlink()

    if os.name == "nt":
        with _word_automation_process_lock():
            _convert_with_word_with_retry(source, target)
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
