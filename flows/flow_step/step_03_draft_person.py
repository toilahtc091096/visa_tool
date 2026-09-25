from api import api_get_draft, api_get_person_info, api_save_person_info
from flows.flow_payloads import build_person_profile, full_name_from_ocr, vietnamese_name_from_ocr
from models import GetDraftListBody, GetDraftListResult, has_name, person_info_result_from_dict
from utils import log_event
from .common import check_api_result, fail_step, get_in


async def load_draft_and_prepare_person(ctx, client) -> bool:
    ctx.step = "get_draft"
    has_provided_first_applyid = bool(getattr(ctx, "first_applyid", None))
    body_draft = GetDraftListBody()
    ok1, meta1 = await api_get_draft(client, ctx.token, ctx.tmp_secret, body_draft)
    if not await check_api_result(ctx, ok1, meta1):
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
        if not await check_api_result(ctx, ok2, meta2):
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
    if not ctx.first_applyid:
        ctx.first_applyid = obj.applyid if obj else ""
    print("applyid=", ctx.first_applyid)

    if not ctx.first_applyid:
        return await fail_step(
            ctx, "missing applyid in response", response=resp1
        )

    ctx.step = "get_current_draft_personal_information"
    ctx.data_obj = {}
    ok, meta = await api_get_person_info(
        client, ctx.token, ctx.tmp_secret, ctx.first_applyid
    )
    if ok:
        parsed = person_info_result_from_dict(meta.get("response") or {})
        if parsed.Response is not None and parsed.Response.Data is not None:
            ctx.data_obj = parsed.Response.Data

    return True
 