import random

import httpx

from api import (
    api_get_draft,
    api_passport_ocr,
    api_save_apply_info,
    api_save_person_info,
)
from constants import DEFAULT_EMBASSY, DEFAULT_LANG
from models import (
    ApplyInfoProfile,
    GetDraftListBody,
    GetDraftListResult,
    PersonInfoProfile,
    has_name,
    passport_ocr_result_from_dict,
)
from utils import log_event, notify


async def run_flow(
    base_url: str,
    token: str,
    tmp_secret: str,
    file_path: str,
    province_city_code: str,
    id_card_number: str,
) -> None:
    async with httpx.AsyncClient() as client:
        # STEP 0: get ocr to getinformation name:
        step = "get ocr"
        ok, meta = await api_passport_ocr(
            client=client,
            base_url=base_url,
            token=token,
            tmp_secret=tmp_secret,
            file_path=file_path,
            form_field_name="file",
        )

        log_event({"step": step, "ok": ok, **meta})
        resp = meta.get("response")
        if isinstance(resp, dict):
            ocr_data = passport_ocr_result_from_dict(resp)
        else:
            await notify(
                f"Flow FAILED at step={step}. status={meta.get('status_code')} "
                f"err={meta.get('error')}"
            )
            return

        # STEP 1: get_draft
        step = "get_draft"
        body_draft = GetDraftListBody()
        ok1, meta1 = await api_get_draft(client, base_url, token, tmp_secret, body_draft)
        log_event({"step": step, "ok": ok1, **meta1})
        if not ok1:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta1.get('status_code')} "
                f"err={meta1.get('error')}"
            )
            return

        resp1 = meta1.get("response", {})
        result = GetDraftListResult.from_dict(resp1)

        full_name = " ".join(
            filter(
                None,
                [
                    ocr_data.Response.Data.passportFirstName
                    if ocr_data.Response.Data
                    else None,
                    ocr_data.Response.Data.passportFamilyName
                    if ocr_data.Response.Data
                    else None,
                ],
            )
        )
        if not has_name(result, full_name):
            log_event(
                {
                    "step": step,
                    "ok": False,
                    "error": "Missing user_name in response",
                    "response": resp1,
                }
            )
            await notify(f"Flow FAILED at step={step}: missing user_id in response")
            return

        obj = next(
            (
                it
                for it in result.Response.Data.list
                if (it.name or "").strip() == full_name
            ),
            None,
        )
        first_applyid = obj.applyid if obj else ""
        print("applyid=", first_applyid)
        if not first_applyid:
            log_event(
                {
                    "step": step,
                    "ok": False,
                    "error": "Missing applyid in response",
                    "response": resp1,
                }
            )
            await notify(f"Flow FAILED at step={step}: missing applyid in response")
            # GOI API TAO MOI DE LAY APPLYID MOI
            return

        # STEP 2: save_personal_information (only if step1 success)
        step = "save_personal_information"

        ocr = ocr_data.Response.Data

        person_json = {
            "applyid": first_applyid,
            "photoDetectionResult": 0,  # không quan trọng
            "childrenFlag": False,  # không quan trọng
            "applyCountry": "",  # không quan trọng
            "finishedStep": 9,  # không quan trọng
            "embassy": DEFAULT_EMBASSY,  # không quan trọng
            "tempSaveFlag": False,  # không quan trọng
            "userId": "",  # không quan trọng
            "birthplaceCounty": "",  # không quan trọng
            "joinNationalityDate": "",  # không quan trọng
            "otherName": "",  # không quan trọng 1.1C
            "formerName": "",  # không quan trọng 1.1D
            "chineseName": "",  # không quan trọng
            "otherSpecify": "",  # không quan trọng
            "haveOtherNationalityFlag": False,  # không quan trọng
            "notApplyItems": [],  # không quan trọng
            "otherNationals": [],  # không quan trọng
            "havePermanentFlag": False,  # không quan trọng
            "haveFormerNationalityFlag": False,  # không quan trọng
            "permanentCountries": "",  # không quan trọng
            "formerNationals": [],  # không quan trọng
            "issueUnit": "",  # không quan trọng
            "issueDate": "",  # không quan trọng
            "lostPassportFlag": "",  # không quan trọng
            "lostPassports": [],  # không quan trọng
            "localName": "",  # không quan trọng
            "lang": DEFAULT_LANG,  # không quan trọng
            "otherPassportinfo": "",  # không quan trọng
            "birthday": ocr.dateOfBirth if ocr else None,  # 1.2  OCR
            "birthplaceCountry": ocr.issuingCountry if ocr else None,  # 1.4A OCR
            "passportFamilyName": ocr.passportFamilyName if ocr else None,  # 1.1A OCR
            "passportFirstName": ocr.passportFirstName if ocr else None,  # 1.1B OCR
            "gender": ocr.sex if ocr else None,  # 1.3 OCR
            "nationalityCountry": ocr.nationality if ocr else None,  # 1.6A OCR
            "passportNumber": ocr.passportNumber if ocr else None,  # 1.7B OCR
            "expirationDate": ocr.dateOfExpiration if ocr else None,  # 1.7E OCR
            "issueCountry": ocr.issuingCountry if ocr else None,  # 1.7C OCR
            # Fake ra, cần lấy tất cả các giá trị ở đây để làm list fake 706001 - 706005 (706001 và 706003 )
            "maritalStatus": random.choice(["706001", "706003"]),
            # 1.7A cần  lấy tất cả các giá trị ở đây để làm list fake 707001 -> 707006 ( không chọn vào 707006 ưu tiên 2 cái đầu)
            "passport": random.choice(["707001", "707002"]),
            # 1.7D, có vài loại thông tin này, cần lấy ra hết
            "issuePlace": random.choice(["CQLXNC", "CUC QUAN LY XNC"]),
            "photoPath": "",  # tim cach lay sau hoac la tu len trang de upload
            "passportPath": "",  # tim cach lay sau hoac la tu len trang de upload
            "birthplaceProvince": province_city_code,  # 1.4B Chưa lấy được
            "birthplaceCity": province_city_code,  # 1.4C Chưa lấy được
            "nationalityIdcard": id_card_number,  # 1.6B Chưa lấy được
        }
        body_save_person_infor = PersonInfoProfile.from_dict(person_json)
        ok2, meta2 = await api_save_person_info(
            client, base_url, token, tmp_secret, body_save_person_infor
        )
        log_event({"step": step, "ok": ok2, **meta2})

        if not ok2:
            await notify(
                f"Flow FAILED at step={step}. status={meta2.get('status_code')} "
                f"err={meta2.get('error')}"
            )
            return
        # STEP 3: save_type_of_visa
        step = "save_type_of_visa"

        apply_info_json = {
            "travelAgencyLicenseNo": "",
            "finishedStep": 9,
            "embassy": DEFAULT_EMBASSY,
            "applyCountry": "",

            # ===== VISA INFO (replace per run / UX) =====
            "visaPurpose": "709001",
            "serviceType": "701001",
            "applyVisaValidity": "3",
            "applyMaxStayDays": "15",
            "applyVisaTimes": "703001",
            "visaType": "710001",

            "tempSaveFlag": False,
            "userId": "",

            "applyReason": {
                "missionName": "",
                "name": "",
                "newPredecessorFlag": "",
                "otherSpecify": "",
                "personalMatters": "",
                "predecessorName": "",
                "relation": "",
                "residencePermit": "",
                "residentName": "",
                "talentProgrammeName": "",
                "travelAgencyLicenseNo": "",
                "travelAgencyName": "",
            },

            "applyid": first_applyid,
            "notApplyItems": [],

            "groupVisaFlag": True,

            "lang": DEFAULT_LANG,
        }

        body_save_apply_info = ApplyInfoProfile.from_dict(apply_info_json)

        ok3, meta3 = await api_save_apply_info(
            client,
            base_url,
            token,
            tmp_secret,
            body_save_apply_info,
        )

        log_event(
            {
                "step": step,
                "ok": ok3,
                **meta3,
            }
        )
        # su dung type o day de setting file theo list

        if not ok3:
            await notify(
                f"Flow FAILED at step={step}. "
                f"status={meta3.get('status_code')} "
                f"err={meta3.get('error')}"
            )
            return

    # await notify("Flow SUCCESS: all steps completed.")
