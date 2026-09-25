from api import api_remove_upload_file
from utils import (
    api_upload_file_common,
    ensure_data_folder_downloaded,
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
    ctx.profile.prepare_resources(ctx)
    selected_upload_keys = set(upload_config_keys or [])

    for item in ctx.profile.upload_plan():
        if is_update_info and item.doc_type not in selected_upload_keys:
            continue

        if is_update_info:
            for f_doc in item.codes:
                ok_remove, meta_remove = await api_remove_upload_file(
                    client,
                    ctx.token,
                    ctx.tmp_secret,
                    f_doc["categoryCode"],
                    f_doc["materialCode"],
                    ctx.first_applyid,
                )
                ctx.step = f"remove_upload_file {item.doc_type}"
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

        all_upload_files = [
            f for cfg in item.configs for f in get_files(cfg["folder"], cfg["limit"])
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
