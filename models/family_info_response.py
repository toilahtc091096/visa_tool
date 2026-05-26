from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class NotApplyItem:
    notApplyCode: str
    remark: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "NotApplyItem":
        return NotApplyItem(
            notApplyCode=str(d.get("notApplyCode", "") or ""),
            remark=str(d.get("remark", "") or ""),
        )


@dataclass(slots=True)
class FamilyMemberItem:
    sort: str
    relation: str
    familyName: str
    firstName: str
    nationalityCountry: str
    profession: str
    otherSpecify: str
    birthday: str
    inChinaFlag: bool
    statusInChina: str
    statusInChinaDetail: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FamilyMemberItem":
        return FamilyMemberItem(
            sort=str(d.get("sort", "") or ""),
            relation=str(d.get("relation", "") or ""),
            familyName=str(d.get("familyName", "") or ""),
            firstName=str(d.get("firstName", "") or ""),
            nationalityCountry=str(d.get("nationalityCountry", "") or ""),
            profession=str(d.get("profession", "") or ""),
            otherSpecify=str(d.get("otherSpecify", "") or ""),
            birthday=str(d.get("birthday", "") or ""),
            inChinaFlag=bool(d.get("inChinaFlag", False)),
            statusInChina=str(d.get("statusInChina", "") or ""),
            statusInChinaDetail=str(d.get("statusInChinaDetail", "") or ""),
        )


@dataclass(slots=True)
class GetFamilyInfoData:
    applyid: str
    tempSaveFlag: bool
    finishedStep: int
    notApplyItems: list[NotApplyItem]

    country: str
    province: str
    city: str
    county: str
    streetAddr: str
    phoneNumber: str
    mobilePhoneNumber: str
    email: str

    relativeRelativeFlag: bool

    spouses: list[FamilyMemberItem]
    parents: list[FamilyMemberItem]
    children: list[FamilyMemberItem]
    relatives: list[FamilyMemberItem]

    haveSpouseFlag: bool

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetFamilyInfoData":
        return GetFamilyInfoData(
            applyid=str(d.get("applyid", "") or ""),
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            finishedStep=int(d.get("finishedStep", 0) or 0),
            notApplyItems=[NotApplyItem.from_dict(x) for x in (d.get("notApplyItems") or [])],

            country=str(d.get("country", "") or ""),
            province=str(d.get("province", "") or ""),
            city=str(d.get("city", "") or ""),
            county=str(d.get("county", "") or ""),
            streetAddr=str(d.get("streetAddr", "") or ""),
            phoneNumber=str(d.get("phoneNumber", "") or ""),
            mobilePhoneNumber=str(d.get("mobilePhoneNumber", "") or ""),
            email=str(d.get("email", "") or ""),

            relativeRelativeFlag=bool(d.get("relativeRelativeFlag", False)),

            spouses=[FamilyMemberItem.from_dict(x) for x in (d.get("spouses") or [])],
            parents=[FamilyMemberItem.from_dict(x) for x in (d.get("parents") or [])],
            children=[FamilyMemberItem.from_dict(x) for x in (d.get("children") or [])],
            relatives=[FamilyMemberItem.from_dict(x) for x in (d.get("relatives") or [])],

            haveSpouseFlag=bool(d.get("haveSpouseFlag", False)),
        )


@dataclass(slots=True)
class GetFamilyInfoResponseWrapper:
    Data: Optional[GetFamilyInfoData]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetFamilyInfoResponseWrapper":
        data = d.get("Data")
        return GetFamilyInfoResponseWrapper(
            Data=GetFamilyInfoData.from_dict(data) if isinstance(data, dict) else None
        )


@dataclass(slots=True)
class GetFamilyInfoResponse:
    Response: Optional[GetFamilyInfoResponseWrapper]
    raw: dict[str, Any]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetFamilyInfoResponse":
        resp = d.get("Response")
        return GetFamilyInfoResponse(
            Response=GetFamilyInfoResponseWrapper.from_dict(resp) if isinstance(resp, dict) else None,
            raw=d,
        )

    @property
    def data(self) -> Optional[GetFamilyInfoData]:
        return self.Response.Data if self.Response and self.Response.Data else None