from api import api_remove_upload_file
from constants import UPLOAD_CONFIG, UPLOAD_FILE_CODE_BY_VISA_TYPE
from utils import api_upload_file_common, ensure_data_folder_downloaded, get_files
from utils import log_event, notify


async def upload_files(
    ctx,
    client,
    is_update_info: bool = False,
    upload_config_keys=None,
) -> bool:
    ctx.step = "Step 9 Upload File"
    ensure_data_folder_downloaded(ctx.passportNumber)
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
                    log_event(
                        {
                            "step": "remove_upload_file",
                            "ok": ok_remove,
                            "doc_type": doc_type,
                            **meta_remove,
                        }
                    )
                    if not ok_remove:
                        await notify(
                            f"Flow FAILED at step=remove_upload_file. "
                            f"status={meta_remove.get('status_code')} "
                            f"err={meta_remove.get('error')}"
                        )
                        return False

            configs = config if isinstance(config, list) else [config]
            all_upload_files = []
            for cfg in configs:
                upload_files = get_files(cfg["folder"], cfg["limit"])
                all_upload_files.extend(upload_files)

            for f_doc, upload_file in zip(files, all_upload_files):
                if not upload_file:
                    continue
                print(upload_file, f_doc["categoryCode"], f_doc["materialCode"])
                await api_upload_file_common(
                    client,
                    ctx.token,
                    ctx.tmp_secret,
                    upload_file,
                    f_doc["categoryCode"],
                    f_doc["materialCode"],
                    ctx.first_applyid,
                )
    return True
 
