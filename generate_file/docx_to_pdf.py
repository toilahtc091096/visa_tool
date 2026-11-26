from __future__ import annotations

import atexit
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


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


def _env_number(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


class WordKeeper:
    """
    One Word kept open in this process, owned by one long-lived thread.

    Opening Word is the slow part of a conversion (several seconds), and a case
    converts 2-6 files. Word is opened on the first file, reused for the next
    ones, and closed after WORD_IDLE_SECONDS (default 600) without a file; the
    next case opens it again. Also restarted after WORD_MAX_CONVERSIONS files
    and after any error. A file taking longer than WORD_CONVERT_TIMEOUT_SECONDS
    gets that Word killed. WORD_KEEP_ALIVE=0 goes back to one Word per file.

    COM objects belong to the thread that made them, so every Word call happens
    on the worker thread; callers queue a job and wait for it.
    """

    poll_seconds = 0.5

    def __init__(self, idle_seconds: float, max_conversions: int, timeout_seconds: float) -> None:
        self.idle_seconds = idle_seconds
        self.max_conversions = max_conversions
        self.timeout_seconds = timeout_seconds
        self._jobs: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._start_lock = threading.Lock()
        self._pid: int | None = None
        self.is_open = False   # for tests / status

    # --- hooks (Word through COM; tests replace them) ---
    def _com_init(self) -> None:
        import pythoncom
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)

    def _com_uninit(self) -> None:
        import pythoncom
        pythoncom.CoUninitialize()

    def _pump(self) -> None:
        import pythoncom
        pythoncom.PumpWaitingMessages()

    def _open_word(self) -> Any:
        import win32com.client
        before = _word_pids()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        new = _word_pids() - before
        # Opened while holding the machine-wide mutex: the only new WINWORD is ours.
        self._pid = next(iter(new)) if len(new) == 1 else None
        return word

    def _alive(self, word: Any) -> bool:
        try:
            word.Documents.Count
            return True
        except Exception:
            return False

    def _export(self, word: Any, source: Path, target: Path) -> None:
        document = word.Documents.Open(str(source), ConfirmConversions=False, ReadOnly=True, AddToRecentFiles=False)
        try:
            document.ExportAsFixedFormat(str(target), 17)   # wdExportFormatPDF
        finally:
            try:
                document.Close(False)
            except Exception:
                pass

    def _quit(self, word: Any) -> None:
        try:
            word.Quit()
        except Exception:
            self.kill()

    def kill(self) -> None:
        pid, self._pid = self._pid, None
        if pid:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)

    # --- worker ---
    def _log(self, action: str, **extra: Any) -> None:
        try:
            from utils import log_event
            log_event({"step": "word_keepalive", "action": action, "pid": self._pid, **extra})
        except Exception:
            pass

    def _ensure_thread(self) -> None:
        with self._start_lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name="word-keeper", daemon=True)
                self._thread.start()

    def _run(self) -> None:
        self._com_init()
        word, count = None, 0

        def close(reason: str) -> None:
            nonlocal word, count
            if word is not None:
                self._log("close", reason=reason, files=count)
                self._quit(word)
            word, count, self.is_open = None, 0, False
            self._pid = None

        try:
            idle_since = time.monotonic()
            while True:
                try:
                    # Short waits with the thread's messages handled in between: a COM
                    # thread that never handles them can hang programs that broadcast.
                    job = self._jobs.get(timeout=self.poll_seconds)
                except queue.Empty:
                    self._pump()
                    if word is not None and time.monotonic() - idle_since >= self.idle_seconds:
                        close("idle")
                    continue
                if job is None:
                    close("shutdown")
                    return
                source, target, done, box = job
                try:
                    if word is not None and (count >= self.max_conversions or not self._alive(word)):
                        close("recycle" if count >= self.max_conversions else "dead")
                    if word is None:
                        word = self._open_word()
                        self.is_open = True
                        self._log("open")
                    self._export(word, source, target)
                    count += 1
                except BaseException as exc:  # noqa: BLE001 - handed to the caller
                    box["error"] = exc
                    close("error")
                finally:
                    idle_since = time.monotonic()
                    done.set()
        finally:
            self._com_uninit()

    def convert(self, source: Path, target: Path) -> None:
        self._ensure_thread()
        done, box = threading.Event(), {}
        self._jobs.put((source, target, done, box))
        if not done.wait(self.timeout_seconds):
            self._log("timeout", file=source.name)
            self.kill()                      # the stuck COM call fails, the worker resets Word
            done.wait(30)
            raise RuntimeError(f"Microsoft Word did not finish '{source.name}' in {self.timeout_seconds:.0f}s")
        if "error" in box:
            exc = box["error"]
            raise RuntimeError(f"Microsoft Word could not convert '{source}' to PDF: {exc}") from exc

    def shutdown(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self._jobs.put(None)
            self._thread.join(10)


def _word_pids() -> set[int]:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq WINWORD.EXE", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    pids = set()
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            pids.add(int(parts[1]))
    return pids


_KEEPER: WordKeeper | None = None
_KEEPER_LOCK = threading.Lock()


def _word_keep_alive() -> bool:
    return os.getenv("WORD_KEEP_ALIVE", "1").strip().lower() not in {"0", "false", "no", "off"}


def _keeper() -> WordKeeper:
    global _KEEPER
    with _KEEPER_LOCK:
        if _KEEPER is None:
            _KEEPER = WordKeeper(
                idle_seconds=_env_number("WORD_IDLE_SECONDS", 600),
                max_conversions=int(_env_number("WORD_MAX_CONVERSIONS", 50)),
                timeout_seconds=_env_number("WORD_CONVERT_TIMEOUT_SECONDS", 180),
            )
            atexit.register(_KEEPER.shutdown)
        return _KEEPER


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
            if _word_keep_alive():
                _keeper().convert(source, target)   # Word kept open between files
            else:
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
        from utils import log_event

        wait_started_at = time.perf_counter()
        with _word_automation_process_lock():
            convert_started_at = time.perf_counter()
            _convert_with_word_with_retry(source, target)
        log_event(
            {
                "step": "timing",
                "phase": "word_docx_to_pdf",
                "file": source.name,
                "lock_wait_seconds": round(convert_started_at - wait_started_at, 2),
                "convert_seconds": round(time.perf_counter() - convert_started_at, 2),
            }
        )
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
