from dataclasses import dataclass, field
from typing import Any


@dataclass
class MilitaryServiceInfo:
    serviceCountry: str = ""
    branchOfService: str = ""
    rank: str = ""
    startDate: str = ""
    endDate: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "MilitaryServiceInfo":
        return MilitaryServiceInfo(
            serviceCountry=d.get("serviceCountry", "") or "",
            branchOfService=d.get("branchOfService", "") or "",
            rank=d.get("rank", "") or "",
            startDate=d.get("startDate", "") or "",
            endDate=d.get("endDate", "") or "",
        )


@dataclass
class OtherInfoItem:
    sort: str = ""
    itemValue: bool = False
    itemNote: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "OtherInfoItem":
        return OtherInfoItem(
            sort=d.get("sort", "") or "",
            itemValue=bool(d.get("itemValue", False)),
            itemNote=d.get("itemNote", "") or "",
        )


@dataclass
class OtherInformationProfile:
    applyCountry: str

    finishedStep: int

    embassy: str

    tempSaveFlag: bool

    userId: str

    militaryServiceInfos: list[MilitaryServiceInfo] = field(default_factory=list)

    otherInfoItems: list[OtherInfoItem] = field(default_factory=list)

    itemValue3: str = ""

    applyid: str = ""

    notApplyItems: list[Any] = field(default_factory=list)

    otherProblemFlag: bool = False

    lang: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "OtherInformationProfile":
        return OtherInformationProfile(
            applyCountry=d.get("applyCountry", "") or "",

            finishedStep=int(d.get("finishedStep", 0) or 0),

            embassy=d.get("embassy", "") or "",

            tempSaveFlag=bool(d.get("tempSaveFlag", False)),

            userId=d.get("userId", "") or "",

            militaryServiceInfos=[
                MilitaryServiceInfo.from_dict(item)
                for item in (d.get("militaryServiceInfos") or [])
            ],

            otherInfoItems=[
                OtherInfoItem.from_dict(item)
                for item in (d.get("otherInfoItems") or [])
            ],

            itemValue3=d.get("itemValue3", "") or "",

            applyid=d.get("applyid", "") or "",

            notApplyItems=list(d.get("notApplyItems") or []),

            otherProblemFlag=bool(
                d.get("otherProblemFlag", False)
            ),

            lang=d.get("lang", "") or "",
        )