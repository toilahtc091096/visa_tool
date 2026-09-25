import time

from api import api_get_education_info, api_passport_ocr, login
from constants import OLD_APPLY_ID_FOR_TEST_TOKEN, PASSPORT_FILE_FOLDER
from models import passport_ocr_result_from_dict
from .common import check_api_result, fail_step
from utils import (
    get_passport_file_path,
    log_event,
    save_login_data,
    date_util,
)


async def check_token_and_get_ocr(ctx, client) -> bool:
    ctx.step = "check token"
    ok, _ = await api_get_education_info(
        client=client,
        token=ctx.token,
        tmp_secret=ctx.tmp_secret,
        applyid=OLD_APPLY_ID_FOR_TEST_TOKEN,
    )
    if not ok:
        print("call login")
        login_started_at = time.perf_counter()
        login_response = login(ctx.authorization)
        log_event(
            {
                "step": "timing",
                "phase": "login",
                "seconds": round(time.perf_counter() - login_started_at, 2),
            }
        )
        print(login_response)
        save_login_data(login_response.data)
        if login_response.data:
            ctx.token = login_response.data.token
            ctx.tmp_secret = login_response.data.tmpSecret
    else:
        print("token ok ")

    ctx.step = "get ocr"
    if PASSPORT_FILE_FOLDER in (None, ""):
        return await fail_step(ctx, "PASSPORT_FILE_FOLDER is not configured")
    ctx.profile.prepare_resources(ctx)
    data_passport_number = getattr(ctx, "input_passportNumber", ctx.passportNumber)
    passport_file_path = get_passport_file_path(
        PASSPORT_FILE_FOLDER, prefix=data_passport_number
    )
    if not passport_file_path:
        return await fail_step(
            ctx, f"passport image not found on R2 for prefix {data_passport_number!r}"
        )

    ok, meta = await api_passport_ocr(
        client=client,
        token=ctx.token,
        tmp_secret=ctx.tmp_secret,
        file_path=passport_file_path,
        form_field_name="file",
    )
    if not await check_api_result(ctx, ok, meta):
        return False

    resp = meta.get("response")
    ctx.ocr_data = passport_ocr_result_from_dict(resp if isinstance(resp, dict) else {})
    ocr_response = getattr(ctx.ocr_data, "Response", None)
    ocr_data = getattr(ocr_response, "Data", None)
    file_id = (getattr(ocr_data, "fileId", "") or "").strip()
    if not ocr_data or not file_id:
        return await fail_step(
            ctx,
            "OCR missing fileId, maybe need check file passport in R2",
            status_code=meta.get("status_code"),
            response=resp,
        )

    ctx.fileId = file_id
    ctx.is_under_18 = False
    if ocr_data.dateOfBirth is not None:
        ctx.is_under_18 = date_util.is_under_18(ocr_data.dateOfBirth)
        ctx.passportNumber = ocr_data.passportNumber

    return True
