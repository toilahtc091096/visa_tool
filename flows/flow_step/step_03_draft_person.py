from api import api_get_draft, api_get_person_info, api_save_person_info
from flows.flow_payloads import build_person_profile, full_name_from_ocr, vietnamese_name_from_ocr
from models import GetDraftListBody, GetDraftListResult, has_name, person_info_result_from_dict
from utils import log_event
from .common import check_api_result, extract_api_error, fail_step, get_in

TOKEN_HINT = "Có thể token đã hết hạn: lấy token mới rồi chạy lại."


def _api_problem(ok: bool, meta: dict) -> str:
    """Why an API call gave nothing usable ("" when it is fine)."""
    response = meta.get("response")
    err = extract_api_error(response)
    if err:
        return " ".join(str(v) for v in (err.get("code"), err.get("message")) if v)
    if not ok:
        detail = meta.get("error") or (str(response)[:300] if response else "")
        return f"HTTP {meta.get('status_code')} {detail}".strip()
    return ""


async def load_draft_and_prepare_person(ctx, client) -> bool:
    ctx.step = "get_draft"
    has_provided_first_applyid = bool(getattr(ctx, "first_applyid", None))
    body_draft = GetDraftListBody()
    ok1, meta1 = await api_get_draft(client, ctx.token, ctx.tmp_secret, body_draft)
    log_event({"step": ctx.step, "ok": ok1, **meta1})
    problem = _api_problem(ok1, meta1)
    if not problem and get_in(meta1, "response", "Response", "_no_data"):
        problem = "COVA không trả về Data"
    if problem:
        # Without the draft list the run would not find the old profile: it would make
        # a new one and lose the old information. Stop and say why.
        return await fail_step(
            ctx,
            f"Không lấy được danh sách hồ sơ nháp (GetDraftList) nên không lấy được thông tin cũ. "
            f"{TOKEN_HINT} Chi tiết: {problem}",
            status_code=meta1.get("status_code"),
            response=meta1.get("response"),
        )

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
    problem = _api_problem(ok, meta)
    if problem:
        # The later steps would fill the form without the old information.
        return await fail_step(
            ctx,
            f"Không đọc được thông tin cũ của hồ sơ nháp applyid={ctx.first_applyid} (GetPersonInfo). "
            f"{TOKEN_HINT} Chi tiết: {problem}",
            status_code=meta.get("status_code"),
            response=meta.get("response"),
        )
    parsed = person_info_result_from_dict(meta.get("response") or {})
    if parsed.Response is not None and parsed.Response.Data is not None:
        ctx.data_obj = parsed.Response.Data

    return True
 