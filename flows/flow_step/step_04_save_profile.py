from api import api_save_apply_info, api_save_person_info
from flows.flow_payloads import build_apply_info_profile, build_person_profile
from .common import check_api_result


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
    if not await check_api_result(ctx, ok2, meta2):
        return False

    ctx.step = "save_type_of_visa"
    body_save_apply_info = build_apply_info_profile(
        ctx.first_applyid,
        ctx.first_letter_visa_type,
        ctx.last_letter_visa_type,
        ctx.entries_type,
        ctx.type_of_visa_sub_value,
        ctx.service_type,
        apply_visa_validity=getattr(ctx, "apply_visa_validity", None),
        inviter_family_name=getattr(ctx, "inviterFamilyName", ""),
        inviter_given_name=getattr(ctx, "inviterGivenName", ""),
        inviter_id_card=getattr(ctx, "inviterIdCard", ""),
        inviter_relation=getattr(ctx, "inviterRelation", ""),
    )
    ok3, meta3 = await api_save_apply_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_apply_info,
    )
    if not await check_api_result(ctx, ok3, meta3):
        return False

    return True
 
