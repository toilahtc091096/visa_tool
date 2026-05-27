from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersonInfoData:
    applyid: str | None = None
    tempSaveFlag: bool | None = None
    finishedStep: int | None = None

    notApplyItems: list[Any] = field(default_factory=list)

    passportFamilyName: str | None = None
    passportFirstName: str | None = None
    formerName: str | None = None
    localName: str | None = None
    chineseName: str | None = None

    birthday: str | None = None
    gender: int | None = None

    birthplaceCountry: str | None = None
    birthplaceProvince: str | None = None
    birthplaceCity: str | None = None
    birthplaceCounty: str | None = None

    maritalStatus: str | None = None
    otherSpecify: str | None = None

    nationalityCountry: str | None = None
    nationalityIdcard: str | None = None
    joinNationalityDate: str | None = None

    havePermanentFlag: bool | None = None
    permanentCountries: str | None = None

    haveOtherNationalityFlag: bool | None = None
    haveFormerNationalityFlag: bool | None = None

    passport: str | None = None
    otherPassportinfo: str | None = None

    passportNumber: str | None = None
    issueCountry: str | None = None
    issuePlace: str | None = None
    issueUnit: str | None = None

    expirationDate: str | None = None

    photoPath: str | None = None
    photoUrl: str | None = None
    photoDetectionResult: int | None = None

    passportPath: str | None = None
    passportUrl: str | None = None

    otherNationals: list[Any] = field(default_factory=list)
    formerNationals: list[Any] = field(default_factory=list)
    lostPassports: list[Any] = field(default_factory=list)

    childrenFlag: bool | None = None


@dataclass
class PersonInfoError:
    Code: str | None = None
    Message: str | None = None


@dataclass
class PersonInfoResponse:
    Data: PersonInfoData | None = None
    Error: PersonInfoError | None = None


@dataclass
class PersonInfoResult:
    Response: PersonInfoResponse


def person_info_result_from_dict(d: dict[str, Any]) -> PersonInfoResult:
    resp = (d or {}).get("Response") or {}

    err = resp.get("Error")
    error_obj = None
    if isinstance(err, dict):
        error_obj = PersonInfoError(
            Code=err.get("Code"),
            Message=err.get("Message"),
        )

    data = resp.get("Data")
    data_obj = None
    if isinstance(data, dict):
        data_obj = PersonInfoData(
            applyid=data.get("applyid"),
            tempSaveFlag=data.get("tempSaveFlag"),
            finishedStep=data.get("finishedStep"),
            notApplyItems=data.get("notApplyItems") or [],

            passportFamilyName=data.get("passportFamilyName"),
            passportFirstName=data.get("passportFirstName"),
            formerName=data.get("formerName"),
            localName=data.get("localName"),
            chineseName=data.get("chineseName"),

            birthday=data.get("birthday"),
            gender=data.get("gender"),

            birthplaceCountry=data.get("birthplaceCountry"),
            birthplaceProvince=data.get("birthplaceProvince"),
            birthplaceCity=data.get("birthplaceCity"),
            birthplaceCounty=data.get("birthplaceCounty"),

            maritalStatus=data.get("maritalStatus"),
            otherSpecify=data.get("otherSpecify"),

            nationalityCountry=data.get("nationalityCountry"),
            nationalityIdcard=data.get("nationalityIdcard"),
            joinNationalityDate=data.get("joinNationalityDate"),

            havePermanentFlag=data.get("havePermanentFlag"),
            permanentCountries=data.get("permanentCountries"),

            haveOtherNationalityFlag=data.get("haveOtherNationalityFlag"),
            haveFormerNationalityFlag=data.get("haveFormerNationalityFlag"),

            passport=data.get("passport"),
            otherPassportinfo=data.get("otherPassportinfo"),

            passportNumber=data.get("passportNumber"),
            issueCountry=data.get("issueCountry"),
            issuePlace=data.get("issuePlace"),
            issueUnit=data.get("issueUnit"),

            expirationDate=data.get("expirationDate"),

            photoPath=data.get("photoPath"),
            photoUrl=data.get("photoUrl"),
            photoDetectionResult=data.get("photoDetectionResult"),

            passportPath=data.get("passportPath"),
            passportUrl=data.get("passportUrl"),

            otherNationals=data.get("otherNationals") or [],
            formerNationals=data.get("formerNationals") or [],
            lostPassports=data.get("lostPassports") or [],

            childrenFlag=data.get("childrenFlag"),
        )

    return PersonInfoResult(
        Response=PersonInfoResponse(Data=data_obj, Error=error_obj)
    )