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

DATA_RESOURCE_DIR = Path(__file__).resolve().parent / ".." / "resources"
DATA_R2_PREFIX = "data/"
_DOWNLOADED_PREFIXES: set[str] = set()
_DOWNLOADED_BUSINESS_FOLDERS: set[str] = set()
_CURRENT_DATA_FOLDER: Path | None = None


def _sanitize_folder_suffix(value: str) -> str:
    text = str(value or "").strip().strip('"').strip("'")
    text = "".join(ch for ch in text if ch.isalnum() or ch in {"_", "-"})
    return text or "default"


def _passport_data_dir(prefix: str) -> Path:
    return DATA_RESOURCE_DIR / f"data_{_sanitize_folder_suffix(prefix)}"


def ensure_data_folder_downloaded(
    prefix: str = DATA_R2_PREFIX,
    extra_prefixes: list[str] | tuple[str, ...] | None = None,
) -> None:
    global _CURRENT_DATA_FOLDER
    prefixes = [prefix, *(extra_prefixes or [])]
    for item in prefixes:
        normalized = str(item or "").strip()
        if not normalized:
            continue
        target_dir = _passport_data_dir(normalized)
        if normalized in _DOWNLOADED_PREFIXES and target_dir.exists():
            _CURRENT_DATA_FOLDER = target_dir
            continue
        download_r2_folder(prefix=normalized, local_dir=str(target_dir))
        _DOWNLOADED_PREFIXES.add(normalized)
        _CURRENT_DATA_FOLDER = target_dir


def cleanup_data_folder() -> None:
    global _DOWNLOADED_PREFIXES, _DOWNLOADED_BUSINESS_FOLDERS
    global _CURRENT_DATA_FOLDER
    for path in sorted(DATA_RESOURCE_DIR.glob("data_*"), reverse=True):
        if path.is_dir():
            for item in sorted(path.rglob("*"), reverse=True):
                if item.is_file() or item.is_symlink():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    item.rmdir()
            path.rmdir()

    business_dir = DATA_RESOURCE_DIR / "doanh-nghiep"
    if business_dir.exists() and business_dir.is_dir():
        for item in sorted(business_dir.rglob("*"), reverse=True):
            if item.is_file() or item.is_symlink():
                item.unlink(missing_ok=True)
            elif item.is_dir():
                item.rmdir()
        business_dir.rmdir()

    _DOWNLOADED_PREFIXES = set()
    _DOWNLOADED_BUSINESS_FOLDERS = set()
    _CURRENT_DATA_FOLDER = None


def get_files(folder_path, x):
    relative_folder = folder_path.lstrip("/\\")
    search_bases = []
    if _CURRENT_DATA_FOLDER:
        search_bases.append(_CURRENT_DATA_FOLDER)
    search_bases.append(DATA_RESOURCE_DIR)

    folder = None
    for folder_base in search_bases:
        candidate = folder_base / relative_folder
        if candidate.exists() and candidate.is_dir():
            folder = candidate
            break

    if folder is None:
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
        _CURRENT_DATA_FOLDER
        if not folder_name or folder_name.lower() == "resrouces/data"
        else (_CURRENT_DATA_FOLDER or DATA_RESOURCE_DIR) / folder_name
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
    search_roots = []
    passport_dir = folder / "passport"
    if passport_dir.exists() and passport_dir.is_dir():
        search_roots.append(passport_dir)
    search_roots.append(folder)

    def _find_first_image(paths):
        for root in paths:
            for p in root.rglob("*"):
                if p.is_file() and p.suffix.lower() in image_extensions:
                    return p
        return None

    first_file = _find_first_image(search_roots)
    if first_file is None:
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


def ensure_company_doanh_nghiep_downloaded(company_passport: str) -> None:
    normalized = str(company_passport or "").strip().strip('"').strip("'")
    if not normalized:
        print("[company_download] skip: empty company_passport")
        return

    target_key = normalized
    if target_key in _DOWNLOADED_BUSINESS_FOLDERS:
        print(f"[company_download] skip: already downloaded {normalized}")
        return

    print(
        f"[company_download] downloading prefix={normalized}/doanh-nghiep "
        f"to local_dir={DATA_RESOURCE_DIR / 'doanh-nghiep'}"
    )
    download_r2_folder(
        prefix=f"{normalized}/doanh-nghiep",
        local_dir=str(DATA_RESOURCE_DIR / "doanh-nghiep"),
    )
    _DOWNLOADED_BUSINESS_FOLDERS.add(target_key)
    print(f"[company_download] done: {normalized}")
