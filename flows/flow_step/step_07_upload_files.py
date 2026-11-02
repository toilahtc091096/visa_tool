from pathlib import Path

from api import api_remove_upload_file
from constants import PASSPORT_FILE_FOLDER
from utils import (
    api_upload_file_common,
    ensure_data_folder_downloaded,
    get_files,
    get_passport_file_path,
)
from utils import log_event
from .common import check_api_result, fail_step


def _source_files(cfg: dict, data_passport_number: str) -> list[Path]:
    if "first_of" in cfg:
        for source in cfg["first_of"]:
            files = _source_files(source, data_passport_number)
            if files:
                return files
        return []
    if cfg.get("passport_image"):
        path = get_passport_file_path(PASSPORT_FILE_FOLDER, prefix=data_passport_number)
        return [Path(path)] if path else []
    return get_files(cfg["folder"], cfg["limit"])


async def upload_files(
    ctx,
    client,
    is_update_info: bool = False,
    upload_config_keys=None,
) -> bool:
    ctx.step = "Step 9 Upload File"
    data_passport_number = getattr(ctx, "input_passportNumber", ctx.passportNumber)
    ensure_data_folder_downloaded(data_passport_number)
    ctx.profile.prepare_resources(ctx)
    selected_upload_keys = set(upload_config_keys or [])

    for item in ctx.profile.upload_plan():
        all_upload_files = [
            f
            for cfg in item.configs
            for f in _source_files(cfg, data_passport_number)
        ]
        for f_doc, upload_file in zip(item.codes, all_upload_files):
            if not upload_file:
                continue
            ctx.step = (
                f"upload_file {item.doc_type} "
                f"{f_doc['categoryCode']}/{f_doc['materialCode']} {upload_file.name}"
            )
            ok, meta = await api_upload_file_common(
                client,
                ctx.token,
                ctx.tmp_secret,
                upload_file,
                f_doc["categoryCode"],
                f_doc["materialCode"],
                ctx.first_applyid,
            )
            if not await check_api_result(ctx, ok, meta):
                return False
    return True
