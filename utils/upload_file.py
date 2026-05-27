from pathlib import Path
from flows.flow_payloads import (
    build_upload_material_body,
)
from api import (
    api_upload_file,
)

from utils import (
    log_event,
    notify,
)

from constants import PASSPORT_FILE_FOLDER
def get_files(folder_path, x):
    base = Path(__file__).resolve().parent / ".." / "resources"

    folder = base / folder_path.lstrip("/")

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

from pathlib import Path

def get_passport_file_path()-> str :
    folder = Path(PASSPORT_FILE_FOLDER)

    first_file = next((p for p in folder.iterdir() if p.is_file()), None)

    file_path = str(first_file) if first_file else None
    return(file_path)