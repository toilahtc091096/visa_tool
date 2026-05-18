from dataclasses import dataclass, field
from typing import Any


@dataclass
class FamilyParent:
    sort: str = ""
    relation: str = ""
    familyName: str = ""
    firstName: str = ""
    nationalityCountry: str = ""
    profession: str = ""
    otherSpecify: str = ""
    birthday: str = ""
    inChinaFlag: bool = False
    statusInChina: str = ""
    statusInChinaDetail: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FamilyParent":
        return FamilyParent(
            sort=d.get("sort", "") or "",
            relation=d.get("relation", "") or "",
            familyName=d.get("familyName", "") or "",
            firstName=d.get("firstName", "") or "",
            nationalityCountry=d.get("nationalityCountry", "") or "",
            profession=d.get("profession", "") or "",
            otherSpecify=d.get("otherSpecify", "") or "",
            birthday=d.get("birthday", "") or "",
            inChinaFlag=bool(d.get("inChinaFlag", False)),
            statusInChina=d.get("statusInChina", "") or "",
            statusInChinaDetail=d.get("statusInChinaDetail", "") or "",
        )


@dataclass
class FamilySpouse:
    address: str = ""
    birthCity: str = ""
    birthCountry: str = ""
    birthCounty: str = ""
    familyName: str = ""
    firstName: str = ""
    nationalityCountry: str = ""
    profession: str = ""
    birthday: str = ""
    sort: int = 1
    country: str = ""
    province: str = ""
    city: str = ""
    county: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FamilySpouse":
        return FamilySpouse(
            address=d.get("address", "") or "",
            birthCity=d.get("birthCity", "") or "",
            birthCountry=d.get("birthCountry", "") or "",
            birthCounty=d.get("birthCounty", "") or "",
            familyName=d.get("familyName", "") or "",
            firstName=d.get("firstName", "") or "",
            nationalityCountry=d.get("nationalityCountry", "") or "",
            profession=d.get("profession", "") or "",
            birthday=d.get("birthday", "") or "",
            sort=int(d.get("sort", 1) or 1),
            country=d.get("country", "") or "",
            province=d.get("province", "") or "",
            city=d.get("city", "") or "",
            county=d.get("county", "") or "",
        )


@dataclass
class FamilyChild:
    tt1: bool = False
    tt2: str = ""
    familyName: str = ""
    firstName: str = ""
    nationalityCountry: str = ""
    profession: str = ""
    address: str = ""
    birthday: str = ""
    dd2: str = ""
    dd3: str = ""
    country: str = ""
    province: str = ""
    city: str = ""
    county: str = ""
    statusInChina: str = ""
    statusInChinaDetail: str = ""
    inChinaFlag: bool | None = None
    sort: int = 1

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FamilyChild":
        raw_in_china = d.get("inChinaFlag")
        in_china = None if raw_in_china is None else bool(raw_in_china)
        return FamilyChild(
            tt1=bool(d.get("tt1", False)),
            tt2=d.get("tt2", "") or "",
            familyName=d.get("familyName", "") or "",
            firstName=d.get("firstName", "") or "",
            nationalityCountry=d.get("nationalityCountry", "") or "",
            profession=d.get("profession", "") or "",
            address=d.get("address", "") or "",
            birthday=d.get("birthday", "") or "",
            dd2=d.get("dd2", "") or "",
            dd3=d.get("dd3", "") or "",
            country=d.get("country", "") or "",
            province=d.get("province", "") or "",
            city=d.get("city", "") or "",
            county=d.get("county", "") or "",
            statusInChina=d.get("statusInChina", "") or "",
            statusInChinaDetail=d.get("statusInChinaDetail", "") or "",
            inChinaFlag=in_china,
            sort=int(d.get("sort", 1) or 1),
        )


@dataclass
class FamilyInfoProfile:
    applyCountry: str
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str
    haveSpouseFlag: bool
    country: str
    province: str
    city: str
    county: str
    zipCode: str
    mobilePhoneNumber: str
    phoneNumber: str
    email: str
    streetAddr: str
    relativeRelativeFlag: bool
    applyid: str
    lang: str

    notApplyItems: list[Any] = field(default_factory=list)
    spouses: list[FamilySpouse] = field(default_factory=list)
    children: list[FamilyChild] = field(default_factory=list)
    relatives: list[Any] = field(default_factory=list)
    parents: list[FamilyParent] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FamilyInfoProfile":
        return FamilyInfoProfile(
            applyCountry=d.get("applyCountry", "") or "",
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",
            haveSpouseFlag=bool(d.get("haveSpouseFlag", False)),
            country=d.get("country", "") or "",
            province=d.get("province", "") or "",
            city=d.get("city", "") or "",
            county=d.get("county", "") or "",
            zipCode=d.get("zipCode", "") or "",
            mobilePhoneNumber=d.get("mobilePhoneNumber", "") or "",
            phoneNumber=d.get("phoneNumber", "") or "",
            email=d.get("email", "") or "",
            streetAddr=d.get("streetAddr", "") or "",
            relativeRelativeFlag=bool(d.get("relativeRelativeFlag", False)),
            applyid=d.get("applyid", "") or "",
            lang=d.get("lang", "") or "",
            notApplyItems=list(d.get("notApplyItems") or []),
            spouses=[FamilySpouse.from_dict(item) for item in (d.get("spouses") or [])],
            children=[FamilyChild.from_dict(item) for item in (d.get("children") or [])],
            relatives=list(d.get("relatives") or []),
            parents=[FamilyParent.from_dict(item) for item in (d.get("parents") or [])],
        )
