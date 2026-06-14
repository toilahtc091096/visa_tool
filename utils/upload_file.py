from pathlib import Path
from flows.flow_payloads import (
    build_upload_material_body,
)
from api import (
    api_upload_file,
)
from utils.download_r2 import download_r2_folder

from utils import (
    log_event,
    notify,
)

DATA_LOCAL_DIR = Path(__file__).resolve().parent / ".." / "resources" / "data"
DATA_R2_PREFIX = "data/"
_DATA_DOWNLOADED = False


def ensure_data_folder_downloaded(prefix: str = DATA_R2_PREFIX) -> None:
    global _DATA_DOWNLOADED
    if _DATA_DOWNLOADED and DATA_LOCAL_DIR.exists():
        return
    download_r2_folder(prefix=prefix, local_dir=str(DATA_LOCAL_DIR))
    _DATA_DOWNLOADED = True


def cleanup_data_folder() -> None:
    global _DATA_DOWNLOADED
    if DATA_LOCAL_DIR.exists():
        for path in sorted(DATA_LOCAL_DIR.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                path.rmdir()
        DATA_LOCAL_DIR.rmdir()
    _DATA_DOWNLOADED = False


def get_files(folder_path, x):
    folder = DATA_LOCAL_DIR / folder_path.lstrip("/\\")
    if not folder.exists() or not folder.is_dir():
        return []

    files = [f for f in folder.iterdir() if f.is_file()]
    return files[:x]


async def api_upload_file_common(
    client: str,
    token: str,
    tmp_secret: str,
    file_name: str,
    category_code: str,
    material_code: str,
    first_applyid: str,
) -> None:
    ticket_upload_payload_body = build_upload_material_body(
        file_name,
        category_code,
        material_code,
        first_applyid,
    )
    ok9, meta9 = await api_upload_file(
        client,
        token,
        tmp_secret,
        ticket_upload_payload_body,
    )
    log_event({"step": "step", "ok": ok9, **meta9})
    if not ok9:
        await notify(
            f"Flow FAILED at step={'step'}. "
            f"status={meta9.get('status_code')} "
            "err={meta9.get('error')}"
        )
        return


def get_passport_file_path(passport_folder: str, prefix: str) -> str | None:
    ensure_data_folder_downloaded(prefix)

    folder_name = str(passport_folder or "").strip().lstrip("/\\")
    folder = (
        DATA_LOCAL_DIR
        if not folder_name or folder_name.lower() == "resrouces/data"
        else DATA_LOCAL_DIR / folder_name
    )
    if not folder.exists() or not folder.is_dir():
        return None

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".gif",
        ".tif",
        ".tiff",
    }
    first_file = next(
        (
            p
            for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in image_extensions
        ),
        None,
    )

    file_path = str(first_file) if first_file else None
    return file_path
