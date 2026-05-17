from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplyReason:
    missionName: str = ""
    name: str = ""
    newPredecessorFlag: str = ""
    otherSpecify: str = ""
    personalMatters: str = ""
    predecessorName: str = ""
    relation: str = ""
    residencePermit: str = ""
    residentName: str = ""
    talentProgrammeName: str = ""
    travelAgencyLicenseNo: str = ""
    travelAgencyName: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ApplyReason":
        return ApplyReason(
            missionName=d.get("missionName", "") or "",
            name=d.get("name", "") or "",
            newPredecessorFlag=d.get("newPredecessorFlag", "") or "",
            otherSpecify=d.get("otherSpecify", "") or "",
            personalMatters=d.get("personalMatters", "") or "",
            predecessorName=d.get("predecessorName", "") or "",
            relation=d.get("relation", "") or "",
            residencePermit=d.get("residencePermit", "") or "",
            residentName=d.get("residentName", "") or "",
            talentProgrammeName=d.get("talentProgrammeName", "") or "",
            travelAgencyLicenseNo=d.get("travelAgencyLicenseNo", "") or "",
            travelAgencyName=d.get("travelAgencyName", "") or "",
        )


@dataclass
class ApplyInfoProfile:
    travelAgencyLicenseNo: str
    finishedStep: int
    embassy: str
    applyCountry: str

    visaPurpose: str
    serviceType: str
    applyVisaValidity: str
    applyMaxStayDays: str
    applyVisaTimes: str
    visaType: str

    tempSaveFlag: bool
    userId: str

    applyReason: ApplyReason

    applyid: str

    notApplyItems: list[Any] = field(default_factory=list)

    groupVisaFlag: bool = False

    lang: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ApplyInfoProfile":
        return ApplyInfoProfile(
            travelAgencyLicenseNo=d.get("travelAgencyLicenseNo", "") or "",

            finishedStep=int(d.get("finishedStep", 0) or 0),

            embassy=d.get("embassy", "") or "",
            applyCountry=d.get("applyCountry", "") or "",

            visaPurpose=d.get("visaPurpose", "") or "",
            serviceType=d.get("serviceType", "") or "",
            applyVisaValidity=d.get("applyVisaValidity", "") or "",
            applyMaxStayDays=d.get("applyMaxStayDays", "") or "",
            applyVisaTimes=d.get("applyVisaTimes", "") or "",
            visaType=d.get("visaType", "") or "",

            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",

            applyReason=ApplyReason.from_dict(
                d.get("applyReason", {}) or {}
            ),

            applyid=d.get("applyid", "") or "",

            notApplyItems=list(d.get("notApplyItems") or []),

            groupVisaFlag=bool(d.get("groupVisaFlag", False)),

            lang=d.get("lang", "") or "",
        )
