from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PersonInfoProfile:
    photoDetectionResult: int
    childrenFlag: bool
    applyCountry: str
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str

    birthday: str
    birthplaceCity: str
    birthplaceCountry: str
    birthplaceProvince: str
    birthplaceCounty: str
    joinNationalityDate: str

    photoPath: str
    passportPath: str

    passportFamilyName: str
    passportFirstName: str
    otherName: str
    formerName: str
    chineseName: str

    gender: int
    maritalStatus: str
    otherSpecify: str

    nationalityCountry: str
    nationalityIdcard: str
    haveOtherNationalityFlag: bool

    notApplyItems: list[Any] = field(default_factory=list)
    otherNationals: list[Any] = field(default_factory=list)

    havePermanentFlag: bool = False
    haveFormerNationalityFlag: bool = False
    permanentCountries: str = ""
    formerNationals: list[Any] = field(default_factory=list)

    passport: str = ""
    otherPassportinfo: str = ""
    passportNumber: str = ""
    issueCountry: str = ""
    issuePlace: str = ""
    issueUnit: str = ""
    issueDate: str = ""
    expirationDate: str = ""

    lostPassportFlag: Optional[str] = None
    lostPassports: list[Any] = field(default_factory=list)

    applyid: str = ""
    localName: str = ""
    lang: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "PersonInfoProfile":
        return PersonInfoProfile(
            photoDetectionResult=int(d.get("photoDetectionResult", 0) or 0),
            childrenFlag=bool(d.get("childrenFlag", False)),
            applyCountry=d.get("applyCountry", "") or "",
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",

            birthday=d.get("birthday", "") or "",
            birthplaceCity=d.get("birthplaceCity", "") or "",
            birthplaceCountry=d.get("birthplaceCountry", "") or "",
            birthplaceProvince=d.get("birthplaceProvince", "") or "",
            birthplaceCounty=d.get("birthplaceCounty", "") or "",
            joinNationalityDate=d.get("joinNationalityDate", "") or "",

            photoPath=d.get("photoPath", "") or "",
            passportPath=d.get("passportPath", "") or "",

            passportFamilyName=d.get("passportFamilyName", "") or "",
            passportFirstName=d.get("passportFirstName", "") or "",
            otherName=d.get("otherName", "") or "",
            formerName=d.get("formerName", "") or "",
            chineseName=d.get("chineseName", "") or "",

            gender=int(d.get("gender", 0) or 0),
            maritalStatus=d.get("maritalStatus", "") or "",
            otherSpecify=d.get("otherSpecify", "") or "",

            nationalityCountry=d.get("nationalityCountry", "") or "",
            nationalityIdcard=d.get("nationalityIdcard", "") or "",
            haveOtherNationalityFlag=bool(
                d.get("haveOtherNationalityFlag", False)),

            notApplyItems=list(d.get("notApplyItems") or []),
            otherNationals=list(d.get("otherNationals") or []),

            havePermanentFlag=bool(d.get("havePermanentFlag", False)),
            haveFormerNationalityFlag=bool(
                d.get("haveFormerNationalityFlag", False)),
            permanentCountries=d.get("permanentCountries", "") or "",
            formerNationals=list(d.get("formerNationals") or []),

            passport=d.get("passport", "") or "",
            otherPassportinfo=d.get("otherPassportinfo", "") or "",
            passportNumber=d.get("passportNumber", "") or "",
            issueCountry=d.get("issueCountry", "") or "",
            issuePlace=d.get("issuePlace", "") or "",
            issueUnit=d.get("issueUnit", "") or "",
            issueDate=d.get("issueDate", "") or "",
            expirationDate=d.get("expirationDate", "") or "",

            lostPassportFlag=d.get("lostPassportFlag"),
            lostPassports=list(d.get("lostPassports") or []),

            applyid=d.get("applyid", "") or "",
            localName=d.get("localName", "") or "",
            lang=d.get("lang", "") or "",
        )
