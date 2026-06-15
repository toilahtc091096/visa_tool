from api import api_get_draft, api_get_person_info, api_save_person_info
from flows.flow_payloads import build_person_profile, full_name_from_ocr, vietnamese_name_from_ocr
from models import GetDraftListBody, GetDraftListResult, has_name, person_info_result_from_dict
from utils import log_event, notify
from .common import get_in


async def load_draft_and_prepare_person(ctx, client) -> bool:
    ctx.step = "get_draft"
    provided_first_applyid = getattr(ctx, "first_applyid", None)
    has_provided_first_applyid = provided_first_applyid not in (None, "")
    if provided_first_applyid not in (None, ""):
        ctx.first_applyid = provided_first_applyid
    body_draft = GetDraftListBody()
    ok1, meta1 = await api_get_draft(client, ctx.token, ctx.tmp_secret, body_draft)
    log_event({"step": ctx.step, "ok": ok1, **meta1})
    if not ok1:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta1.get('status_code')} "
            f"err={meta1.get('error')}"
        )
        return False

    resp1 = meta1.get("response", {})
    result = GetDraftListResult.from_dict(resp1)
    ctx.full_name = full_name_from_ocr(ctx.ocr_data)
    ctx.vietnamese_name = vietnamese_name_from_ocr(ctx.ocr_data)

    if not has_provided_first_applyid and not has_name(result, ctx.full_name):
        log_event(
            {
                "step": ctx.step,
                "ok": False,
                "error": "Missing user_name in draft, create new",
                "response": resp1,
            }
        )
        ctx.step = "save_personal_information_first"
        body_save_person_infor = build_person_profile(
            "", ctx.ocr_data.Response.Data, ctx.province_city_code, ctx.id_card_number, ctx.passport_type_code, ctx.haveSpouseFlag, ctx.fileId, {}
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
        ctx.first_applyid = get_in(meta2, "response", "Response", "Data", "applyid")

    obj = next(
        (
            it
            for it in result.Response.Data.list
            if (it.name or "").strip() == ctx.full_name
        ),
        None,
    )
    if ctx.first_applyid is None or ctx.first_applyid == "":
        ctx.first_applyid = obj.applyid if obj else ""
    print("applyid=", ctx.first_applyid)

    if not ctx.first_applyid:
        log_event(
            {
                "step": ctx.step,
                "ok": False,
                "error": "Missing applyid in response",
                "response": resp1,
            }
        )
        await notify(f"Flow FAILED at step={ctx.step}: missing applyid in response")
        return False

    ctx.step = "get_current_draft_personal_information"
    ctx.data_obj = {}
    if ctx.first_applyid is None or ctx.first_applyid == "":
        #todo: check it
        ok, result = await api_get_person_info(
            client, ctx.token, ctx.tmp_secret, ctx.first_applyid
        )
        if ok:
            parsed = person_info_result_from_dict(result.get("response") or {})
            ctx.data_obj = parsed.Response.Data

    return True
 