import os
import random
from datetime import date
from typing import Any, Dict
from utils import date_util, log_event, notify, mobile_utils
from dataclasses import asdict, is_dataclass
from typing import Any
from constants import (
    APPLY_VISA_VALIDITY,
    DEFAULT_EMBASSY,
    DEFAULT_LANG,
    ENTRIES_TYPE,
    JOB_TYPE_BY_LABEL,
    PREFER_JOB_TYPE,
    SELF_EMPLOYED_JOB_DESC,
    SERVICE_TYPE_NORMAL_EXPRESS,
    VIETNAMESE_NAMES,
    VISA_TYPE_VALUE,
    EDUCATION_DEGREE_TYPE,
    EDUCATION_SCHOOL_NAMES,
    FAMILY_DEFAULT_PHONE,
    FAMILY_FATHER_NOT_APPLY_REMARK,
    FAMILY_PARENT_RELATION_MOTHER,
    FAMILY_STREET_DISTRICT,
    TRAVEL_ARRIVAL_COUNTY,
    TRAVEL_CITY_CODE,
    TRAVEL_EMERGENCY_RELATION,
    TRAVEL_INVITE_NAMES,
    TRAVEL_INVITE_PROVINCE,
    TRAVEL_INVITE_RELATION_HOTEL,
    TRAVEL_PAY_FOR_SELF,
    TRAVEL_PAY_FOR_OTHER,
    ALLOWED_CHINA_VISA_TYPES,
    L_15_HOTEL_INFO,
    MALE_VIETNAMESE_NAMES,
    FEMALE_VIETNAMESE_NAMES,
    FAMILY_PARENT_RELATION_FATHER,
    GIVEN_MALE_VIETNAMESE_NAMES,
    VIETNAM_ADMIN,
    L_30_HOTEL_INFO,
    PASSPORT_SYMBOL_MAP,
    PASSPORT_TYPE_CODE,
    UNDER_18_HOTEL_INFO,
    EMERGENCY_RELATION_FATHER,
    EMERGENCY_RELATION_MOTHER,
)
from models import (
    ApplyInfoProfile,
    EducationInfoProfile,
    FamilyInfoProfile,
    PassportOCRData,
    PassportOCRResult,
    PersonInfoProfile,
    PreviousTravelInfoProfile,
    TravelInfoProfile,
    WorkInfoProfile,
    UploadMaterialBody,
    OtherInformationProfile,
    OtherInfoItem,
    ContactInfoProfile,
    OnlineApplicationRow,
    WorkExperienceItem,
    EducationExperienceItem,
    PersonInfoData,
)


def full_name_from_ocr(ocr_data: PassportOCRResult) -> str:
    ocr = ocr_data.Response.Data
    return " ".join(
        filter(
            None,
            [
                ocr.passportFirstName if ocr else None,
                ocr.passportFamilyName if ocr else None,
            ],
        )
    )


def vietnamese_name_from_ocr(ocr_data: PassportOCRResult) -> str:
    ocr = ocr_data.Response.Data
    return " ".join(
        filter(
            None,
            [
                ocr.passportFamilyName if ocr else None,
                ocr.passportFirstName if ocr else None,
            ],
        )
    )


def build_person_profile(
    applyid: str,
    ocr: PassportOCRData | None,
    province_city_code: str,
    id_card_number: str,
    passport_type_code: str,
    haveSpouseFlag: bool,
    fileId: str,
    personInfoData: PersonInfoData | None,
) -> PersonInfoProfile:
    photo_path = getattr(personInfoData, "photoPath", None)
    photo_url = getattr(personInfoData, "photoUrl", None)
    photo_detection_result = getattr(personInfoData, "photoDetectionResult", None)
    passport_path = getattr(personInfoData, "passportPath", None)
    passport_url = getattr(personInfoData, "passportUrl", None)
    if passport_path is None or passport_path == "":
        passport_path = fileId
    person_json: dict[str, Any] = {
        "applyid": applyid,
        "childrenFlag": False,
        "applyCountry": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "birthplaceCounty": "",
        "joinNationalityDate": "",
        "otherName": "",
        "formerName": "",
        "chineseName": "",
        "otherSpecify": "",
        "haveOtherNationalityFlag": False,
        "notApplyItems": [],
        "otherNationals": [],
        "havePermanentFlag": False,
        "haveFormerNationalityFlag": False,
        "permanentCountries": "",
        "formerNationals": [],
        "issueUnit": "",
        "issueDate": "",
        "lostPassportFlag": False,
        "lostPassports": [],
        "localName": "",
        "lang": DEFAULT_LANG,
        "otherPassportinfo": "",
        "birthday": ocr.dateOfBirth if ocr else None,
        "birthplaceCountry": ocr.issuingCountry if ocr else None,
        "passportFamilyName": ocr.passportFamilyName if ocr else None,
        "passportFirstName": ocr.passportFirstName if ocr else None,
        "gender": ocr.sex if ocr else None,
        "nationalityCountry": ocr.nationality if ocr else None,
        "passportNumber": ocr.passportNumber if ocr else None,
        "expirationDate": ocr.dateOfExpiration if ocr else None,
        "issueCountry": ocr.issuingCountry if ocr else None,
        "maritalStatus": "706001" if haveSpouseFlag else "706003",
        "passport": get_passport_code(passport_type_code),
        "issuePlace": random.choice(["CQLXNC", "CUC QUAN LY XNC"]),
        "photoPath": photo_path,
        "photoUrl": photo_url,
        "passportPath": passport_path,
        "photoDetectionResult": photo_detection_result,
        "passportUrl": passport_url,
        "birthplaceProvince": province_city_code,
        "birthplaceCity": province_city_code,
        "nationalityIdcard": id_card_number,
    }
    return PersonInfoProfile.from_dict(person_json)


def build_apply_info_profile(
    applyid: str,
    first_letter_visa_type: str,
    last_letter_visa_type: str,
    entries_type: str,
    type_of_visa_sub_value: str,
    service_type: str,
) -> ApplyInfoProfile:
    visa_sub = VISA_TYPE_VALUE.get(first_letter_visa_type, {}).get(
        type_of_visa_sub_value, {}
    )
    apply_info_json: dict[str, Any] = {
        "travelAgencyLicenseNo": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "applyCountry": "",
        "tempSaveFlag": False,
        "userId": "",
        "applyid": applyid,
        "notApplyItems": [],
        "groupVisaFlag": True,
        "lang": DEFAULT_LANG,
        "applyReason": {
            "missionName": "",
            "name": "",
            "newPredecessorFlag": False,
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
        "applyVisaValidity": APPLY_VISA_VALIDITY.get(first_letter_visa_type),
        "applyMaxStayDays": last_letter_visa_type,
        "applyVisaTimes": ENTRIES_TYPE.get(entries_type, {}),
        "visaType": visa_sub.get("visaType"),
        "visaPurpose": visa_sub.get("visaPurpose"),
        "serviceType": SERVICE_TYPE_NORMAL_EXPRESS.get(service_type, {}),
    }
    return ApplyInfoProfile.from_dict(apply_info_json)


def _work_experience_entry(
    begin_date: str,
    end_date: str,
    province_city_code: str,
    job_position: str,
    job_duty: str,
) -> dict[str, Any]:
    return {
        "sort": "1",
        "beginDate": begin_date,
        "endDate": end_date,
        "jobName": random.choice(VIETNAMESE_NAMES).upper(),
        "jobAddr": province_city_code,
        "jobTel": mobile_utils.generate_job_tel(),
        "jobPosition": job_position,
        "jobDuty": job_duty,
        "supervisorName": random.choice(VIETNAMESE_NAMES).upper(),
        "supervisorTel": mobile_utils.generate_supervisor_tel(),
    }


def build_work_info_profile(
    applyid: str,
    register_date: date,
    province_city_code: str,
    job_type: str = "",
    experiences: list[WorkExperienceItem] = [],
    is_under_18: bool = False,
) -> WorkInfoProfile:
    job_type_label = random.choice(PREFER_JOB_TYPE)
    job_type_code = JOB_TYPE_BY_LABEL[job_type_label]
    work_begin_date = date_util.work_experience_begin_date(register_date)
    work_end_date = date_util.work_experience_end_date()
    if is_under_18:
        job_type_label = "Student"
        job_type_code = JOB_TYPE_BY_LABEL[job_type_label]

    if job_type_label == "Unemployed":
        not_apply_items = [
            {
                "notApplyCode": "workExperience",
                "remark": "NOI TRO",
            }
        ]
        work_experience: list[dict[str, Any]] = []
    elif job_type_label == "Self-employed":
        not_apply_items = []
        work_experience = [
            _work_experience_entry(
                work_begin_date,
                work_end_date,
                province_city_code,
                SELF_EMPLOYED_JOB_DESC,
                SELF_EMPLOYED_JOB_DESC,
            )
        ]
    elif job_type_label == "Student":
        work_experience: list[dict[str, Any]] = []
        not_apply_items = [
            {
                "notApplyCode": "workExperience",
                "remark": "CON NHO",
            }
        ]
    else:
        not_apply_items = []
        work_experience = [
            _work_experience_entry(
                work_begin_date,
                work_end_date,
                province_city_code,
                "TU KINH DOANH",
                "TU KINH DOANH",
            )
        ]
    we_src = []
    if experiences != []:
        for experience in experiences:
            experience.endDate = work_end_date
            we_src = experiences if experiences != [] else work_experience
    else:
        we_src = work_experience
    if is_under_18:
        work_experience: list[dict[str, Any]] = []
        not_apply_items = [
            {
                "notApplyCode": "workExperience",
                "remark": "CON NHO",
            }
        ]

    work_info_json: dict[str, Any] = {
        "applyCountry": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "otherSpecify": "",
        "d3": False,
        "annualIncome": "",
        "currency": "",
        "notApplyItems": not_apply_items,
        "workExperience": [_to_dict(i) for i in (we_src or [])],
        "applyid": applyid,
        "lang": DEFAULT_LANG,
        "jobType": job_type if job_type != "" else job_type_code,
    }
    return WorkInfoProfile.from_dict(work_info_json)


def _to_dict(x: Any) -> dict[str, Any]:
    if isinstance(x, dict):
        return x
    if is_dataclass(x):
        return asdict(x)
    # fallback: object có attribute
    return dict(vars(x))


def _education_experience_entry(province_city_code: str) -> dict[str, Any]:
    _, degree_code, specialty = random.choice(EDUCATION_DEGREE_TYPE)
    return {
        "sort": "1",
        "beginDate": "",
        "endDate": "",
        "schoolName": f"THPT {random.choice(EDUCATION_SCHOOL_NAMES)}, {province_city_code}",
        "schoolAddr": "",
        "highestDegree": degree_code,
        "specialty": specialty,
    }


def build_education_info_profile(
    applyid: str,
    province_city_code: str,
    educationExperience: list[EducationExperienceItem],
    is_under_18: bool = False,
) -> EducationInfoProfile:

    we_src = []
    not_apply_items = []
    if educationExperience != []:
        we_src = (
            educationExperience
            if educationExperience != []
            else [_education_experience_entry(province_city_code)]
        )
    else:
        we_src = [_education_experience_entry(province_city_code)]

    if is_under_18:
        we_src = []
        not_apply_items = [
            {
                "notApplyCode": "educationExperience",
                "remark": "CON NHO",
            }
        ]
    education_json: dict[str, Any] = {
        "applyCountry": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "language": "",
        "notApplyItems": not_apply_items,
        "educationExperience": [_to_dict(i) for i in (we_src or [])],
        "applyid": applyid,
        "lang": DEFAULT_LANG,
    }
    return EducationInfoProfile.from_dict(education_json)


def _parent_birthday(main_account_birth_date: date) -> str:
    years_before = random.randint(20, 25)
    year = main_account_birth_date.year - years_before
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date_util.iso_date_str(date(year, month, day))


def _empty_spouse_entry() -> dict[str, Any]:
    return {
        "sort": "1",
        "familyName": "",
        "firstName": "",
        "nationalityCountry": "",
        "profession": "",
        "otherSpecify": "",
        "birthCountry": "",
        "birthCity": "",
        "birthday": "",
        "address": "",
    }


def _infor_spouse_entry(
    spouseFamilyName: str = "",
    spouseFirstName: str = "",
    spouseNationalityCountry: str = "",
    spouseBirthday: str = "",
    spouseBirthCountry: str = "",
    spouseBirthCity: str = "",
) -> dict[str, Any]:
    return {
        "sort": "1",
        "familyName": spouseFamilyName,
        "firstName": spouseFirstName,
        "nationalityCountry": spouseNationalityCountry,
        "profession": "",
        "otherSpecify": "",
        "birthCity": spouseBirthCity,
        "birthCounty": spouseBirthCountry,
        "address": spouseBirthCity,
        "birthday": spouseBirthday,
    }


def _child_entry(
    childFamilyName: str = "",
    childGivenName: str = "",
    childNationality: str = "",
    childBirthDate: str = "",
) -> dict[str, Any]:
    return {
        "tt1": False,
        "tt2": "",
        "familyName": childFamilyName.upper(),
        "firstName": childGivenName.upper(),
        "nationalityCountry": childNationality.upper(),
        "profession": "",
        "address": "",
        "birthday": childBirthDate.upper(),
        "dd2": "",
        "dd3": "",
        "country": "",
        "province": "",
        "city": "",
        "county": "",
        "statusInChina": "",
        "statusInChinaDetail": "",
        "inChinaFlag": None,
        "sort": 1,
    }


def build_family_info_profile(
    applyid: str,
    province_city_code: str,
    main_account_birth_date: date,
    family_nationality: str,
    haveSpouseFlag: bool,
    spouseFamilyName: str = "",
    spouseFirstName: str = "",
    spouseNationalityCountry: str = "",
    spouseBirthday: str = "",
    spouseBirthCountry: str = "",
    spouseBirthCity: str = "",
    haveChildFlag: bool = False,
    childFamilyName: str = "",
    childGivenName: str = "",
    childNationality: str = "",
    childBirthDate: str = "",
    fatherFamilyName: str = "",
    fatherGivenName: str = "",
    fatherNationality: str = "",
    fatherBirthDate: str = "",
    motherFamilyName: str = "",
    motherGivenName: str = "",
    motherNationality: str = "",
    motherBirthDate: str = "",
    passportFamilyName: str = "",
    old_notApplyItems=[],
    old_streetAddr: str = "",
    old_phoneNumber: str = "",
    old_mobilePhoneNumber: str = "",
    old_parents=[],
    old_children=[],
    old_relatives=[],
    old_haveSpouseFlag=False,
    old_spouses=[],
) -> FamilyInfoProfile:

    not_apply_items = []
    spouses_info = []
    parents_info = []
    parent_female_family, parent_female_first = _emergency_female_contact_names()
    phone = mobile_utils.generate_supervisor_tel(FAMILY_DEFAULT_PHONE)
    if haveSpouseFlag is not True:
        not_apply_items.append(
            {
                "notApplyCode": "spouse",
                "remark": "",
            }
        )
        spouses_info = [_empty_spouse_entry()]
    else:
        spouses_info = [
            _infor_spouse_entry(
                spouseFamilyName,
                spouseFirstName,
                spouseNationalityCountry,
                spouseBirthday,
                spouseBirthCountry,
                spouseBirthCity,
            )
        ]

    if haveChildFlag is not True:
        not_apply_items.append(
            {
                "notApplyCode": "children",
                "remark": "",
            }
        )
        child_info = []
    else:
        print("have child")
        if childNationality == "":
            childNationality = family_nationality
        child_info = [
            _child_entry(
                childFamilyName, childGivenName, childNationality, childBirthDate
            )
        ]
        print(child_info)

    if fatherFamilyName == "" and fatherGivenName == "":
        if random.randint(0, 9) < 3:
            not_apply_items.append(
                {
                    "notApplyCode": "father",
                    "remark": FAMILY_FATHER_NOT_APPLY_REMARK,
                },
            )
        else:
            parents_info.append(
                {
                    "sort": "1",
                    "relation": FAMILY_PARENT_RELATION_FATHER,
                    "familyName": passportFamilyName,
                    "firstName": random.choice(GIVEN_MALE_VIETNAMESE_NAMES).upper(),
                    "nationalityCountry": family_nationality.upper(),
                    "profession": "",
                    "otherSpecify": "",
                    "birthday": _parent_birthday(main_account_birth_date),
                    "inChinaFlag": False,
                    "statusInChina": "",
                    "statusInChinaDetail": "",
                    "tt1": False,
                    "tt2": "",
                    "profession": "",
                    "address": "",
                    "dd2": "",
                    "dd3": "",
                    "country": "",
                    "province": "",
                    "city": "",
                    "county": "",
                }
            )
    else:
        parents_info.append(
            {
                "sort": "1",
                "relation": FAMILY_PARENT_RELATION_FATHER,
                "familyName": fatherFamilyName,
                "firstName": fatherGivenName,
                "nationalityCountry": family_nationality.upper(),
                "profession": "",
                "otherSpecify": "",
                "birthday": fatherBirthDate,
                "inChinaFlag": False,
                "statusInChina": "",
                "statusInChinaDetail": "",
                "tt1": False,
                "tt2": "",
                "profession": "",
                "address": "",
                "dd2": "",
                "dd3": "",
                "country": "",
                "province": "",
                "city": "",
                "county": "",
            }
        )
    if motherFamilyName == "" and motherGivenName == "":
        parents_info.append(
            {
                "sort": "1",
                "relation": FAMILY_PARENT_RELATION_MOTHER,
                "familyName": parent_female_family,
                "firstName": parent_female_first,
                "nationalityCountry": family_nationality.upper(),
                "profession": "",
                "otherSpecify": "",
                "birthday": _parent_birthday(main_account_birth_date),
                "inChinaFlag": False,
                "statusInChina": "",
                "statusInChinaDetail": "",
            }
        )

    else:
        parents_info.append(
            {
                "sort": "1",
                "relation": FAMILY_PARENT_RELATION_MOTHER,
                "familyName": motherFamilyName,
                "firstName": motherGivenName,
                "nationalityCountry": family_nationality.upper(),
                "profession": "",
                "otherSpecify": "",
                "birthday": motherBirthDate,
                "inChinaFlag": False,
                "statusInChina": "",
                "statusInChinaDetail": "",
            }
        )

    parents_src = []
    if old_parents != []:
        parents_src = old_parents if old_parents != [] else parents_info
    else:
        parents_src = parents_info

    relative_src = []
    if old_relatives != []:
        relative_src = old_relatives if old_relatives != [] else []
    else:
        relative_src = []

    notApplyItems_src = []
    if old_notApplyItems != []:
        notApplyItems_src = (
            old_notApplyItems if old_notApplyItems != [] else not_apply_items
        )
    else:
        notApplyItems_src = not_apply_items

    children_src = []
    if old_children != []:
        children_src = old_children if old_children != [] else child_info
    else:
        children_src = child_info

    spouses_src = []
    if old_spouses != []:
        spouses_src = old_spouses if old_spouses != [] else spouses_info
    else:
        spouses_src = spouses_info

    family_json: dict[str, Any] = {
        "applyCountry": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "country": "",
        "province": "",
        "city": "",
        "county": "",
        "zipCode": "",
        "mobilePhoneNumber": (
            old_mobilePhoneNumber if old_mobilePhoneNumber != "" else phone
        ),
        "phoneNumber": old_phoneNumber if old_phoneNumber != "" else phone,
        "email": "",
        "streetAddr": (
            old_streetAddr
            if old_streetAddr != ""
            else (
                f"{random.choice(VIETNAM_ADMIN[province_city_code])}, {province_city_code}"
                if VIETNAM_ADMIN.get(province_city_code)
                else province_city_code
            )
        ),
        "notApplyItems": [_to_dict(i) for i in (notApplyItems_src or [])],
        "haveSpouseFlag": (
            old_haveSpouseFlag
            if old_haveSpouseFlag
            else ("" if haveSpouseFlag is not True else haveSpouseFlag)
        ),
        "haveChildFlag": "" if haveSpouseFlag is not True else haveSpouseFlag,
        "spouses": [_to_dict(i) for i in (spouses_src or [])],
        "children": [_to_dict(i) for i in (children_src or [])],
        "relatives": [_to_dict(i) for i in (relative_src or [])],
        "relativeRelativeFlag": False,
        "applyid": applyid,
        "parents": [_to_dict(i) for i in (parents_src or [])],
        "lang": DEFAULT_LANG,
    }
    return FamilyInfoProfile.from_dict(family_json)


def _emergency_contact_names() -> tuple[str, str]:
    parts = random.choice(VIETNAMESE_NAMES).upper().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _emergency_male_contact_names() -> tuple[str, str]:
    parts = random.choice(MALE_VIETNAMESE_NAMES).upper().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _emergency_female_contact_names() -> tuple[str, str]:
    parts = random.choice(FEMALE_VIETNAMESE_NAMES).upper().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def getTravelCommonInfo(
    *,
    applyid: str,
    emergency_family: str,
    emergency_first: str,
    emergency_relation: str,
) -> Dict[str, Any]:
    """
    Build the common (#same) part of travel_json.
    """
    return {
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "disposableFunds": "",
        "disposableFundsCurrency": "",
        "sponsorCity": "",
        "sponsorCountry": "",
        "sponsorCounty": "",
        "sponsorEmail": "",
        "sponsorName": "",
        "sponsorPhoneNumber": "",
        "sponsorProvince": "",
        "sponsorRelation": "",
        "sponsorType": "",
        "sponsorZipCode": "",
        "emergencyCity": "",
        "emergencyContactFamilyName": emergency_family,
        "emergencyContactFirstName": emergency_first,
        "emergencyContactMiddlename": "",
        "emergencyCountry": "",
        "emergencyCounty": "",
        "emergencyEmail": "",
        "emergencyPhoneNumber": mobile_utils.generate_supervisor_tel("0964585356"),
        "emergencyProvince": "",
        "emergencyRelation": (
            TRAVEL_EMERGENCY_RELATION
            if emergency_relation == ""
            else emergency_relation
        ),
        "emergencyStreetAddr": "",
        "emergencyZipCode": "",
        # todo: if under 10 ages, choose OTHER, and add parent information
        "payForTravel": TRAVEL_PAY_FOR_SELF,
        "payForTravelName": "",
        "payForTravelPhoneNumber": "",
        "payForTravelEmail": "",
        "payForTravelOrganizationName": "",
        "payForTravelRelation": "",
        "payForTravelAddr": "",
        "payForTravelCountry": "",
        "havePeersFlag": False,
        "applyid": applyid,
        "lang": DEFAULT_LANG,
    }


def getL15TravelInfo(
    *,
    applyid: str,
    emergency_family: str,
    emergency_first: str,
    emergency_relation: str,
    is_under_18: bool,
    haveChildFlag: bool,
    hotel_type: str,
    arrival_str: str,
    leave_str: str,
    arrivalVehicleType: str,
    leaveVehicleType: str,
) -> Dict[str, Any]:
    """
    Full travel_json = #same + specific (hotel/flight/date) part.
    """
    travel_json: Dict[str, Any] = getTravelCommonInfo(
        applyid=applyid,
        emergency_family=emergency_family,
        emergency_first=emergency_first,
        emergency_relation=emergency_relation,
    )
    item_travel = L_15_HOTEL_INFO[hotel_type]
    if is_under_18 or haveChildFlag:
        item_travel = UNDER_18_HOTEL_INFO[0]
    addr = (item_travel.get("address") or "").strip()
    addr_100 = ""
    if len(addr) > 100:
        cut = addr[:100]
        # nếu ký tự thứ 100 đang nằm giữa 1 từ thì lùi về khoảng trắng gần nhất
        last_space = cut.rfind(" ")
        addr_100 = cut[:last_space].rstrip() if last_space != -1 else cut.rstrip()
    else:
        addr_100 = addr
    travel_json.update(
        {
            "invitationNumber": "",
            "inviteCity": item_travel.get("citySelectedBox"),
            "inviteCounty": "",
            "inviteEmail": "",
            "inviteName": item_travel.get("name"),
            "invitePhoneNumber": mobile_utils.generate_supervisor_tel("15920187600"),
            "inviteProvince": item_travel.get("inviteProvince"),
            "inviteRelation": item_travel.get("relationship"),
            "inviteZipCode": "",
            "travelCompanion": [],
            "notApplyItems": [],
            "arrivalVehicleType": arrivalVehicleType,
            "arrivalCity": item_travel.get("citySelectedBox"),
            "arrivalCounty": item_travel.get("arrivalCounty"),
            "stayCity": "",
            "stayCounty": "",
            "travelAddr": "",
            "stayInfo": [
                {
                    "sort": 1,
                    "stayCity": item_travel.get("citySelectedBox"),
                    "stayCounty": item_travel.get("arrivalCounty"),
                    "travelAddr": addr_100,
                    "arrivalDate": arrival_str,
                    "leaveDate": leave_str,
                }
            ],
            "leaveCity": item_travel.get("citySelectedBox"),
            "leaveCounty": "",
            "leaveDate": leave_str,
            "leaveVehicleType": leaveVehicleType,
            "arrivalDate": arrival_str,
        }
    )

    return travel_json


def getL30TravelInfo(
    *,
    applyid: str,
    emergency_family: str,
    emergency_first: str,
    emergency_relation: str,
    is_under_18: bool,
    haveChildFlag: bool,
    arrival_date: date,
    arrivalVehicleType: str,
    leaveVehicleType: str,
) -> Dict[str, Any]:
    """
    Full travel_json = #same + specific (hotel/flight/date) part.
    """
    travel_json: Dict[str, Any] = getTravelCommonInfo(
        applyid=applyid,
        emergency_family=emergency_family,
        emergency_first=emergency_first,
        emergency_relation=emergency_relation,
    )

    # arrival_str = date_util.build_three_stays(arrival_date)
    stays = date_util.build_three_stays(arrival_date)

    stayInfo = []
    for i, hotel in enumerate(L_30_HOTEL_INFO):
        addr = (L_30_HOTEL_INFO[i].get("address") or "").strip()
        addr_100 = ""
        if len(addr) > 100:
            cut = addr[:100]
            # nếu ký tự thứ 100 đang nằm giữa 1 từ thì lùi về khoảng trắng gần nhất
            last_space = cut.rfind(" ")
            addr_100 = cut[:last_space].rstrip() if last_space != -1 else cut.rstrip()
        else:
            addr_100 = addr
        stayInfo.append(
            {
                "sort": i + 1,
                "stayCity": hotel.get("citySelectedBox"),
                "stayCounty": hotel.get("arrivalCounty"),
                "travelAddr": hotel.get("travelAddr") or hotel.get("addr") or addr_100,
                "arrivalDate": stays[i]["arrivalDate"],
                "leaveDate": stays[i]["leaveDate"],
            }
        )

    travel_json.update(
        {
            "invitationNumber": "",
            "inviteCity": L_30_HOTEL_INFO[0].get("citySelectedBox"),
            "inviteCounty": L_30_HOTEL_INFO[0].get("arrivalCounty"),
            "inviteEmail": "",
            "inviteName": L_30_HOTEL_INFO[0].get("name"),
            "invitePhoneNumber": mobile_utils.generate_supervisor_tel("15920187600"),
            "inviteProvince": L_30_HOTEL_INFO[0].get("inviteProvince"),
            "inviteRelation": L_30_HOTEL_INFO[0].get("relationship"),
            "inviteZipCode": "",
            "travelCompanion": [],
            "notApplyItems": [],
            "arrivalVehicleType": arrivalVehicleType,
            "arrivalCity": L_30_HOTEL_INFO[0].get("citySelectedBox"),
            "arrivalCounty": L_30_HOTEL_INFO[0].get("arrivalCounty"),
            "stayCity": "",
            "stayCounty": "",
            "travelAddr": "",
            "stayInfo": stayInfo,
            "leaveCity": L_30_HOTEL_INFO[-1].get("citySelectedBox"),
            "leaveCounty": L_30_HOTEL_INFO[-1].get("arrivalCounty"),
            "leaveDate": stays[-1]["leaveDate"],
            "leaveVehicleType": leaveVehicleType,
            "arrivalDate": stays[0]["arrivalDate"],
        }
    )

    return travel_json


def build_travel_info_profile(
    visa_type: str,
    applyid: str,
    payName: str,
    payMobile: str,
    is_under_18: bool,
    haveChildFlag: bool,
    fatherFamilyName: str,
    fatherGivenName: str,
    motherFamilyName: str,
    motherGivenName: str,
    arrival_date: date,
    leave_date: date,
    hotel_type: int,
    arrivalVehicleType: str,
    leaveVehicleType: str,
) -> TravelInfoProfile:
    print(f"is_under_18: {is_under_18}, haveChildFlag: {haveChildFlag}")
    arrival_str = date_util.iso_date_str(arrival_date)
    leave_str = date_util.iso_date_str(leave_date)
    emergency_relation = TRAVEL_EMERGENCY_RELATION
    if (
        fatherFamilyName == ""
        and fatherGivenName == ""
        and motherFamilyName == ""
        and motherGivenName == ""
    ):
        emergency_family, emergency_first = _emergency_contact_names()
    if fatherFamilyName != "" and fatherGivenName != "":
        emergency_family = fatherFamilyName
        emergency_first = fatherGivenName
        emergency_relation = EMERGENCY_RELATION_FATHER
    if motherFamilyName != "" and motherGivenName != "":
        emergency_family = motherFamilyName
        emergency_first = motherGivenName
        emergency_relation = EMERGENCY_RELATION_MOTHER
    if visa_type == "L15":
        travel_json: dict[str, Any] = getL15TravelInfo(
            applyid=applyid,
            emergency_family=emergency_family,
            emergency_first=emergency_first,
            emergency_relation=emergency_relation,
            is_under_18=is_under_18,
            haveChildFlag=haveChildFlag,
            hotel_type=hotel_type,
            arrival_str=arrival_str,
            leave_str=leave_str,
            arrivalVehicleType=arrivalVehicleType,
            leaveVehicleType=leaveVehicleType,
        )
    elif visa_type == "L30":
        travel_json: dict[str, Any] = getL30TravelInfo(
            applyid=applyid,
            emergency_family=emergency_family,
            emergency_first=emergency_first,
            emergency_relation=emergency_relation,
            is_under_18=is_under_18,
            haveChildFlag=haveChildFlag,
            arrival_date=arrival_date,
            arrivalVehicleType=arrivalVehicleType,
            leaveVehicleType=leaveVehicleType,
        )
    else:
        travel_json = {}

    if payMobile != "" and payName != "":
        travel_json.update(
            {
                "payForTravel": TRAVEL_PAY_FOR_OTHER,
                "payForTravelName": payName,
                "payForTravelPhoneNumber": payMobile,
                "payForTravelEmail": "",
            }
        )
    return TravelInfoProfile.from_dict(travel_json)


def _previous_travel_base(applyid: str) -> dict[str, Any]:
    return {
        "applyCountry": "",
        "finishedStep": 9,
        "embassy": DEFAULT_EMBASSY,
        "tempSaveFlag": False,
        "userId": "",
        "applyid": applyid,
        "lang": DEFAULT_LANG,
        "notApplyItems": [],
    }


def _build_no_previous_china_travel_body(applyid: str) -> dict[str, Any]:
    """First-time / no prior China travel: all flags False, lists empty."""
    return {
        **_previous_travel_base(applyid),
        "arrivedChinaFlag": False,
        "chinaResidenceLicenseFlag": False,
        "collectFingerprintCountry": "",
        "collectFingerprintDate": "",
        "collectFingerprintFlag": False,
        "collectFingerprintPlace": "",
        "haveChinaVisaFlag": False,
        "haveOtherVisaFlag": False,
        "issueDate": "",
        "issuePlace": "",
        "visitedOtherCountryFlag": False,
        "lostChinaVisaDate": "",
        "lostChinaVisaFlag": False,
        "lostChinaVisaNumber": "",
        "lostChinaVisaPlace": "",
        "otherCountries": "",
        "otherVisas": "",
        "previousTravelInChinaInfos": [],
        "provideChinaVisaDetailFlag": False,
        "residenceLicenseNumber": "",
        "visaNumber": "",
        "visaType": "",
        "firstApplyChinaVisaFlag": False,
    }


def build_previous_china_travel_body(
    applyid: str,
    haveChinaVisaFlag: bool = False,
    old_visaType: str = "",
    old_visaNumber: str = "",
    old_issueDate: str = "",
    old_issuePlace: str = "",
    haveOtherVisaFlag: str = "",
    old_otherVisas: str = "",
    old_otherCountries: str = "",
    collectFingerprintFlag: bool = False,
    chinaResidenceLicenseFlag: bool = False,
) -> dict[str, Any]:
    """Applicant has been to China before: fill prior-visit and visa fields."""

    errs = validate_payload(
        {
            "arrivedChinaFlag": True,
            "haveChinaVisaFlag": haveChinaVisaFlag,
            "visaType": old_visaType,
            "visaNumber": old_visaNumber,
            "issueDate": old_issueDate,
            "issuePlace": old_issuePlace,
            "haveOtherVisaFlag": haveOtherVisaFlag,
            "otherVisas": list_to_csv_country_codes(old_otherVisas),
            "otherCountries": list_to_csv_country_codes(old_otherCountries),
        }
    )

    if errs:
        print("INVALID:")
        log_event(
            {
                "step": "Step 8: SavePreviousTravelInfo",
                "status": f"Validate step previous travel error '{errs}'",
            }
        )
        for e in errs:
            print("-", e)
    return {
        **_previous_travel_base(applyid),
        "arrivedChinaFlag": True,
        "chinaResidenceLicenseFlag": chinaResidenceLicenseFlag,
        "collectFingerprintCountry": "",
        "collectFingerprintDate": "",
        "collectFingerprintFlag": collectFingerprintFlag,
        "collectFingerprintPlace": "",
        "lostChinaVisaDate": "",
        "lostChinaVisaFlag": False,
        "lostChinaVisaNumber": "",
        "lostChinaVisaPlace": "",
        "otherCountries": "",
        "provideChinaVisaDetailFlag": False,
        "residenceLicenseNumber": "",
        "previousTravelInChinaInfos": [
            {
                "sort": 1,
                "arrivalDate": "",
                "leaveDate": "",
                # "stayCity": TRAVEL_CITY_CODE,
                # "stayCounty": TRAVEL_ARRIVAL_COUNTY,
                "arrivalCity": "",
                "arrivalCounty": "",
                "travelAddr": "",
            }
        ],
        "visaNumber": old_visaNumber,
        "visaType": old_visaType,
        "firstApplyChinaVisaFlag": not haveChinaVisaFlag,
        "otherVisas": old_otherVisas,
        "haveChinaVisaFlag": haveChinaVisaFlag,
        "haveOtherVisaFlag": haveOtherVisaFlag,
        "issueDate": old_issueDate,
        "issuePlace": old_issuePlace,
        "visitedOtherCountryFlag": not _is_blank(old_otherCountries),
    }


def build_previous_travel_info_profile(
    applyid: str,
    arrivedChinaFlag: bool = False,
    haveChinaVisaFlag: bool = False,
    old_visaType: str = "",
    old_visaNumber: str = "",
    old_issueDate: str = "",
    old_issuePlace: str = "",
    haveOtherVisaFlag: str = "",
    old_otherVisas: str = "",
    old_otherCountries: str = "",
    collectFingerprintFlag: bool = False,
    chinaResidenceLicenseFlag: bool = False,
) -> PreviousTravelInfoProfile:
    if not arrivedChinaFlag:
        previous_travel_json = _build_no_previous_china_travel_body(applyid)
    else:
        previous_travel_json = build_previous_china_travel_body(
            applyid,
            haveChinaVisaFlag,
            old_visaType,
            old_visaNumber,
            old_issueDate,
            old_issuePlace,
            haveOtherVisaFlag,
            old_otherVisas,
            old_otherCountries,
            collectFingerprintFlag,
            chinaResidenceLicenseFlag
        )
    return PreviousTravelInfoProfile.from_dict(previous_travel_json)


def _is_blank(x: Any) -> bool:
    if x is None:
        return True
    if isinstance(x, str):
        return x.strip() == ""
    if isinstance(x, (list, tuple, set)):
        return len([i for i in x if not _is_blank(i)]) == 0
    return False


def _clean_list(xs):
    if xs is None:
        return []
    if isinstance(xs, str):
        xs = [xs]
    return [str(x).strip().upper() for x in xs if not _is_blank(x)]


def validate_payload(p: dict) -> list[str]:
    """
    Check theo logic boolean flags:
    - haveChinaVisaFlag=True => visaType REQUIRED and must be valid
    - haveOtherVisaFlag=True => otherVisas MUST have >=1 country code
    - otherCountries: optional, nhưng nếu có thì không được chứa rỗng
    Trả về list lỗi (rỗng => hợp lệ)
    """
    errors = []

    arrivedChinaFlag = bool(p.get("arrivedChinaFlag", False))
    haveChinaVisaFlag = bool(p.get("haveChinaVisaFlag", False))
    haveOtherVisaFlag = bool(p.get("haveOtherVisaFlag", False))

    visaType = p.get("visaType")
    otherVisas = _clean_list(p.get("otherVisas"))
    otherCountries = _clean_list(p.get("otherCountries"))

    if haveChinaVisaFlag:
        if _is_blank(visaType):
            errors.append("haveChinaVisaFlag=True nhưng thiếu visaType (required).")
        else:
            vt = str(visaType).strip().upper()
            if vt not in ALLOWED_CHINA_VISA_TYPES:
                errors.append(
                    f"visaType='{visaType}' không hợp lệ (không nằm trong whitelist)."
                )

    if haveOtherVisaFlag:
        if len(otherVisas) == 0:
            errors.append(
                "haveOtherVisaFlag=True nhưng otherVisas rỗng (cần ít nhất 1 mã quốc gia)."
            )

    raw_other_countries = p.get("otherCountries")
    if isinstance(raw_other_countries, (list, tuple)) and any(
        _is_blank(x) for x in raw_other_countries
    ):
        errors.append("otherCountries có phần tử rỗng, cần loại bỏ hoặc không gửi.")

    if (not arrivedChinaFlag) and haveChinaVisaFlag:
        errors.append(
            "arrivedChinaFlag=False nhưng haveChinaVisaFlag=True (kiểm tra lại logic)."
        )

    return errors


def list_to_csv_country_codes(xs, *, upper=True):
    if xs is None:
        return ""
    if isinstance(xs, str):
        return xs.strip().upper() if upper else xs.strip()

    cleaned = []
    for x in xs:
        if x is None:
            continue
        s = str(x).strip()
        if not s:
            continue
        cleaned.append(s.upper() if upper else s)

    return ",".join(cleaned)


def build_upload_material_body(
    file_path: str, categoryCode: str, materialCode: str, businessId: str
) -> UploadMaterialBody:
    return UploadMaterialBody(
        filePath=str(file_path),
        fileName=os.path.basename(str(file_path)),
        categoryCode=categoryCode,
        materialCode=materialCode,
        businessId=businessId,
    )


def build_other_info(
    applyid: str,
) -> OtherInformationProfile:
    other_info_items = [
        OtherInfoItem(
            sort=str(i),
            itemValue=False,
            itemNote="",
        )
        for i in range(1, 12)
    ]

    profile = OtherInformationProfile(
        applyCountry="",
        finishedStep=9,
        embassy=DEFAULT_EMBASSY,
        tempSaveFlag=False,
        userId="",
        militaryServiceInfos=[],
        otherInfoItems=other_info_items,
        itemValue3="",
        applyid=applyid,
        notApplyItems=[],
        otherProblemFlag=False,
        lang=DEFAULT_LANG,
    )

    return profile


def build_signature_body(
    applyid: str,
) -> ContactInfoProfile:

    profile = ContactInfoProfile(
        applyCountry="",
        finishedStep=9,
        embassy=DEFAULT_EMBASSY,
        tempSaveFlag=False,
        userId="",
        agentFlag=False,
        agentName="GIANG SON TRAVEL",
        W2="752001",
        relationship="KHACH HANG",
        agentAddr="HA NOI",
        agentTel="0969588832",
        applyid=applyid,
        lang="en_US",
    )

    return profile


def build_L30_guest_names(guest_name: list[str], vietnamese_name: str) -> list[str]:
    if guest_name == []:
        guest_name = [vietnamese_name]
    while len(guest_name) < 4:
        guest_name.append(random.choice(VIETNAMESE_NAMES).upper())
    return guest_name


def get_passport_code(symbol: str) -> str:
    passport_type = PASSPORT_SYMBOL_MAP.get(symbol)

    if not passport_type:
        return PASSPORT_TYPE_CODE["Ordinary"]

    return PASSPORT_TYPE_CODE.get(passport_type, PASSPORT_TYPE_CODE["Ordinary"])
