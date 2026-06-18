import random
from datetime import datetime

from api import (
    api_get_education_info,
    api_get_family_info,
    api_get_work_info,
    api_list_online_applications,
    api_save_education_info,
    api_save_family_info,
    api_save_work_info,
)
from constants import (
    OLD_APPLY_STATUS_APPROVED,
    HOTEL_DATA,
    WEEK_SKIP_BY_TYPE,
)
from flows.flow_payloads import (
    build_education_info_profile,
    build_family_info_profile,
    build_work_info_profile,
)
from models import (
    GetEducationInfoResponse,
    GetFamilyInfoResponse,
    GetWorkInfoResponse,
    OnlineApplicationListResponse,
    WorkExperienceItem,
)
from utils import date_util, log_event, notify


async def save_family_work_education(ctx, client) -> bool:
    ctx.step = "get_old_list"
    ctx.old_item_id = ""
    if ctx.haveChinaVisaFlag:
        okList, metaList = await api_list_online_applications(
            client,
            ctx.token,
            ctx.tmp_secret,
            ctx.ocr_data.Response.Data.passportNumber,
            authorization=getattr(ctx, "authorization", ""),
        )
        if okList:
            model = OnlineApplicationListResponse.from_dict(metaList["response"])
            for item in model.rows:
                if item.applyStatus == OLD_APPLY_STATUS_APPROVED:
                    ctx.old_item_id = item.applyid
        log_event({"step": ctx.step, "ok": okList, **metaList})
        if not okList:
            await notify(
                f"Flow FAILED at step={ctx.step}. "
                f"status={metaList.get('status_code')} "
                f"err={metaList.get('error')}"
            )
            return False

    ctx.step = "save_work_info"
    ctx.job_type = ""
    ctx.experiences = []
    if ctx.old_item_id != "":
        ok, res = await api_get_work_info(
            client=client,
            token=ctx.token,
            tmp_secret=ctx.tmp_secret,
            applyid=ctx.old_item_id,
        )
        if ok:
            model = GetWorkInfoResponse.from_dict(res["response"])
            data = model.data
            if data:
                ctx.job_type = data.jobType
                ctx.experiences = data.workExperience

    body_save_work_info = build_work_info_profile(
        ctx.first_applyid,
        ctx.register_date,
        (
            ctx.ct08_province_city_code
            if ctx.ct08_province_city_code != ""
            else ctx.province_city_code
        ),
        ctx.job_type,
        ctx.experiences,
        ctx.is_under_18,
    )
    ok4, meta4 = await api_save_work_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_work_info,
    )
    log_event({"step": ctx.step, "ok": ok4, **meta4})
    if not ok4:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta4.get('status_code')} "
            f"err={meta4.get('error')}"
        )
        return False

    ctx.step = "save_education_info"
    ctx.educationExperience = []
    if ctx.old_item_id != "":
        ok, res = await api_get_education_info(
            client=client,
            token=ctx.token,
            tmp_secret=ctx.tmp_secret,
            applyid=ctx.old_item_id,
        )
        if ok:
            model = GetEducationInfoResponse.from_dict(res["response"])
            data = model.data
            if data:
                ctx.educationExperience = data.educationExperience

    body_save_education_info = build_education_info_profile(
        ctx.first_applyid,
        (
            ctx.ct08_province_city_code
            if ctx.ct08_province_city_code != ""
            else ctx.province_city_code
        ),
        ctx.educationExperience,
        ctx.is_under_18,
    )
    ok5, meta5 = await api_save_education_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_education_info,
    )
    log_event({"step": ctx.step, "ok": ok5, **meta5})
    if not ok5:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta5.get('status_code')} "
            f"err={meta5.get('error')}"
        )
        return False

    ctx.step = "save_family_info"
    ctx.old_notApplyItems = []
    ctx.old_streetAddr = ""
    ctx.old_phoneNumber = ""
    ctx.old_mobilePhoneNumber = ""
    ctx.old_parents = []
    ctx.old_children = []
    ctx.old_relatives = []
    ctx.old_haveSpouseFlag = False
    ctx.old_spouses = []
    if ctx.old_item_id != "":
        ok, res = await api_get_family_info(
            client=client,
            token=ctx.token,
            tmp_secret=ctx.tmp_secret,
            applyid=ctx.old_item_id,
        )
        if ok:
            model = GetFamilyInfoResponse.from_dict(res["response"])
            data = model.data
            if data:
                ctx.old_notApplyItems = data.notApplyItems
                ctx.old_streetAddr = data.streetAddr
                ctx.old_phoneNumber = data.phoneNumber
                ctx.old_mobilePhoneNumber = data.mobilePhoneNumber
                ctx.old_parents = data.parents
                ctx.old_children = data.children
                ctx.old_relatives = data.relatives
                ctx.old_haveSpouseFlag = data.haveSpouseFlag
                ctx.old_spouses = data.spouses

    dob = date_util.parse_date(ctx.ocr_data.Response.Data.dateOfBirth)
    if dob is None:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            "status={('data is not valid')} "
            "err={('step 6 cannot parse date')}"
        )
        return False

    body_save_family_info = build_family_info_profile(
        ctx.first_applyid,
        (
            ctx.ct08_province_city_code
            if ctx.ct08_province_city_code != ""
            else ctx.province_city_code
        ),
        datetime.strptime(ctx.ocr_data.Response.Data.dateOfBirth, "%Y-%m-%d").date(),
        ctx.ocr_data.Response.Data.nationality,
        ctx.haveSpouseFlag,
        ctx.spouseFamilyName,
        ctx.spouseFirstName,
        ctx.spouseNationalityCountry,
        ctx.spouseBirthday,
        ctx.spouseBirthCountry,
        ctx.spouseBirthCity,
        ctx.haveChildFlag,
        ctx.childFamilyName,
        ctx.childGivenName,
        ctx.childNationality,
        ctx.childBirthDate,
        ctx.fatherFamilyName,
        ctx.fatherGivenName,
        ctx.fatherNationality,
        ctx.fatherBirthDate,
        ctx.motherFamilyName,
        ctx.motherGivenName,
        ctx.motherNationality,
        ctx.motherBirthDate,
        ctx.ocr_data.Response.Data.passportFamilyName,
        ctx.old_notApplyItems,
        ctx.old_streetAddr,
        ctx.old_phoneNumber,
        ctx.old_mobilePhoneNumber,
        ctx.old_parents,
        ctx.old_children,
        ctx.old_relatives,
        ctx.old_haveSpouseFlag,
        ctx.old_spouses,
    )
    ok6, meta6 = await api_save_family_info(
        client,
        ctx.token,
        ctx.tmp_secret,
        body_save_family_info,
    )
    parents = body_save_family_info.parents or []

    father = next((p for p in parents if p.relation == "727002"), None)
    mother = next((p for p in parents if p.relation == "727003"), None)

    if not ctx.fatherFamilyName and not ctx.fatherGivenName and father:
        ctx.fatherFamilyName = father.familyName
        ctx.fatherGivenName = father.firstName

    if not ctx.motherFamilyName and not ctx.motherGivenName and mother:
        ctx.motherFamilyName = mother.familyName
        ctx.motherGivenName = mother.firstName

    log_event({"step": ctx.step, "ok": ok6, **meta6})
    if not ok6:
        await notify(
            f"Flow FAILED at step={ctx.step}. "
            f"status={meta6.get('status_code')} "
            f"err={meta6.get('error')}"
        )
        return False

    return True
