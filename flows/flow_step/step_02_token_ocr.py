from api import api_get_education_info, api_passport_ocr, login
from constants import OLD_APPLY_ID_FOR_TEST_TOKEN, PASSPORT_FILE_FOLDER
from models import GetEducationInfoResponse, passport_ocr_result_from_dict
from utils import get_passport_file_path, log_event, notify, save_login_data, date_util


async def check_token_and_get_ocr(ctx, client) -> bool:
    ctx.step = "check token"
    ok, res = await api_get_education_info(
        client=client,
        token=ctx.token,
        tmp_secret=ctx.tmp_secret,
        applyid=OLD_APPLY_ID_FOR_TEST_TOKEN,
    )
    if not ok:
        parsed = GetEducationInfoResponse.from_dict(res)
        print("call login")
        login_response = login(ctx.authorization)
        print(login_response)
        save_login_data(login_response.data)
        if login_response.data:
            ctx.token = login_response.data.token
            ctx.tmp_secret = login_response.data.tmpSecret
    else:
        print("token ok ")

    ctx.step = "get ocr"
    if PASSPORT_FILE_FOLDER in (None, ""):
        print("no passport file")
        return False
    passport_file_path = get_passport_file_path(PASSPORT_FILE_FOLDER, prefix=ctx.passportNumber)
    if not passport_file_path:
        await notify(
            f"Flow FAILED at step={ctx.step}. status={getattr(ctx, 'status_code', '')} "
            f"err={getattr(ctx, 'error', '')}"
        )
        log_event({"step": ctx.step, "ok": False, **{"status": "not have file"}})
        return False

    ok, meta = await api_passport_ocr(
        client=client,
        token=ctx.token,
        tmp_secret=ctx.tmp_secret,
        file_path=passport_file_path,
        form_field_name="file",
    )
    log_event({"step": ctx.step, "ok": ok, **meta})
    resp = meta.get("response")
    if isinstance(resp, dict):
        ctx.ocr_data = passport_ocr_result_from_dict(resp)
        ctx.is_under_18 = False
        if (
            ctx.ocr_data is not None
            and ctx.ocr_data.Response is not None
            and ctx.ocr_data.Response.Data is not None
            and ctx.ocr_data.Response.Data.dateOfBirth is not None
        ):
            ctx.is_under_18 = date_util.is_under_18(
                ctx.ocr_data.Response.Data.dateOfBirth
            )
        if (
            ctx.ocr_data is not None
            and ctx.ocr_data.Response is not None
            and ctx.ocr_data.Response.Data is not None
            and ctx.ocr_data.Response.Data.dateOfBirth is not None
        ):
            ctx.passportNumber = ctx.ocr_data.Response.Data.passportNumber
            
        if (
            ctx.ocr_data is not None
            and ctx.ocr_data.Response is not None
            and ctx.ocr_data.Response.Data is not None
            and ctx.ocr_data.Response.Data.fileId is not None
        ):
            ctx.fileId = ctx.ocr_data.Response.Data.fileId
        return True

    await notify(
        f"Flow FAILED at step={ctx.step}. status={meta.get('status_code')} "
        f"err={meta.get('error')}"
    )
    return False
