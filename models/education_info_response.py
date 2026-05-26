from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class EducationExperienceItem:
    sort: str
    beginDate: str
    endDate: str
    schoolName: str
    schoolAddr: str
    highestDegree: str
    specialty: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "EducationExperienceItem":
        return EducationExperienceItem(
            sort=str(d.get("sort", "") or ""),
            beginDate=str(d.get("beginDate", "") or ""),
            endDate=str(d.get("endDate", "") or ""),
            schoolName=str(d.get("schoolName", "") or ""),
            schoolAddr=str(d.get("schoolAddr", "") or ""),
            highestDegree=str(d.get("highestDegree", "") or ""),
            specialty=str(d.get("specialty", "") or ""),
        )


@dataclass(slots=True)
class GetEducationInfoData:
    applyid: str
    tempSaveFlag: bool
    finishedStep: int
    notApplyItems: list[Any]
    language: str
    educationExperience: list[EducationExperienceItem]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetEducationInfoData":
        ee_raw = d.get("educationExperience") or []
        return GetEducationInfoData(
            applyid=str(d.get("applyid", "") or ""),
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            finishedStep=int(d.get("finishedStep", 0) or 0),
            notApplyItems=list(d.get("notApplyItems") or []),
            language=str(d.get("language", "") or ""),
            educationExperience=[EducationExperienceItem.from_dict(x) for x in ee_raw],
        )


@dataclass(slots=True)
class GetEducationInfoResponseWrapper:
    Data: Optional[GetEducationInfoData]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetEducationInfoResponseWrapper":
        data = d.get("Data")
        return GetEducationInfoResponseWrapper(
            Data=GetEducationInfoData.from_dict(data) if isinstance(data, dict) else None
        )


@dataclass(slots=True)
class GetEducationInfoResponse:
    Response: Optional[GetEducationInfoResponseWrapper]
    raw: dict[str, Any]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetEducationInfoResponse":
        resp = d.get("Response")
        return GetEducationInfoResponse(
            Response=GetEducationInfoResponseWrapper.from_dict(resp) if isinstance(resp, dict) else None,
            raw=d,
        )

    @property
    def data(self) -> Optional[GetEducationInfoData]:
        return self.Response.Data if self.Response and self.Response.Data else None