from api import api_save_apply_info, api_save_person_info
from flows.flow_payloads import build_apply_info_profile, build_person_profile
from utils import log_event, notify


async def save_person_and_apply(ctx, client) -> bool:
    ctx.step = "save_personal_information"
    body_save_person_infor = build_person_profile(
        ctx.first_applyid,
        ctx.ocr_data.Response.Data,
        ctx.province_city_code,
        ctx.id_card_number,
        ctx.passport_type_code,
        ctx.haveSpouseFlag,
        ctx.fileId,
        ctx.data_obj,
    )
    ok2, meta2 = await api_save_person_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_person_infor,
    )
    log_event({"step": ctx.step, "ok": ok2, **meta2})
    if not ok2:
        await notify(
            f"Flow FAILED at step={ctx.step}. status={meta2.get('status_code')} "
            f"err={meta2.get('error')}"
        )
        return False

    ctx.step = "save_type_of_visa"
    body_save_apply_info = build_apply_info_profile(
        ctx.first_applyid,
        ctx.first_letter_visa_type,
        ctx.last_letter_visa_type,
        ctx.entries_type,
        ctx.type_of_visa_sub_value,
        ctx.service_type,
    )
    ok3, meta3 = await api_save_apply_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_apply_info,
    )
    log_event({"step": ctx.step, "ok": ok3, **meta3})
    if not ok3:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta3.get('status_code')} "
            f"err={meta3.get('error')}"
        )
        return False

    return True
 