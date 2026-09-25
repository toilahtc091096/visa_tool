from api import api_remove_upload_file
from constants import UPLOAD_CONFIG, UPLOAD_FILE_CODE_BY_VISA_TYPE
from utils import (
    api_upload_file_common,
    ensure_company_doanh_nghiep_downloaded,
    ensure_data_folder_downloaded,
    ensure_school_downloaded,
    get_files,
)
from utils import log_event
from .common import check_api_result, fail_step


async def upload_files(
    ctx,
    client,
    is_update_info: bool = False,
    upload_config_keys=None,
) -> bool:
    ctx.step = "Step 9 Upload File"
    data_passport_number = getattr(ctx, "input_passportNumber", ctx.passportNumber)
    ensure_data_folder_downloaded(data_passport_number)
    if str(getattr(ctx, "visa_type", "")).strip().upper().startswith("M"):
        ensure_company_doanh_nghiep_downloaded(getattr(ctx, "company_passport", ""))
    elif str(getattr(ctx, "visa_type", "")).strip().upper().startswith("F"):
        ensure_school_downloaded(getattr(ctx, "school_passport", ""))
    cfg_file_by_visa_type = UPLOAD_FILE_CODE_BY_VISA_TYPE[ctx.visa_type]
    selected_upload_keys = set(upload_config_keys or [])

    for group_key, group_cfg in cfg_file_by_visa_type.items():
        for doc_type, files in group_cfg.items():
            if is_update_info and doc_type not in selected_upload_keys:
                continue
            config = UPLOAD_CONFIG[ctx.visa_type].get(doc_type)
            if not config:
                continue

            if is_update_info:
                for f_doc in files:
                    ok_remove, meta_remove = await api_remove_upload_file(
                        client,
                        ctx.token,
                        ctx.tmp_secret,
                        f_doc["categoryCode"],
                        f_doc["materialCode"],
                        ctx.first_applyid,
                    )
                    ctx.step = f"remove_upload_file {doc_type}"
                    log_event({"step": ctx.step, "ok": ok_remove, **meta_remove})
                    # Only HTTP failures stop the flow: removing a file that was
                    # never uploaded is expected to come back as a business error.
                    if not ok_remove:
                        return await fail_step(
                            ctx,
                            meta_remove.get("error") or "request failed",
                            status_code=meta_remove.get("status_code"),
                            response=meta_remove.get("response"),
                        )

            configs = config if isinstance(config, list) else [config]
            all_upload_files = [
                f for cfg in configs for f in get_files(cfg["folder"], cfg["limit"])
            ]

            for f_doc, upload_file in zip(files, all_upload_files):
                if not upload_file:
                    continue
                ctx.step = (
                    f"upload_file {doc_type} "
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
