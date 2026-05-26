# models/work_info_response.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class WorkExperienceItem:
    sort: str
    beginDate: str
    endDate: str
    jobName: str
    jobAddr: str
    jobTel: str
    jobPosition: str
    jobDuty: str
    supervisorName: str
    supervisorTel: str

    @staticmethod
    def from_dict(d: "dict[str, Any] | WorkExperienceItem") -> "WorkExperienceItem":
        if isinstance(d, WorkExperienceItem):
            return d
        return WorkExperienceItem(
            sort=str(d.get("sort", "") or ""),
            beginDate=d.get("beginDate", "") or "",
            endDate=d.get("endDate", "") or "",
            jobName=d.get("jobName", "") or "",
            jobAddr=d.get("jobAddr", "") or "",
            jobTel=d.get("jobTel", "") or "",
            jobPosition=d.get("jobPosition", "") or "",
            jobDuty=d.get("jobDuty", "") or "",
            supervisorName=d.get("supervisorName", "") or "",
            supervisorTel=d.get("supervisorTel", "") or "",
        )


@dataclass(slots=True)
class GetWorkInfoData:
    applyid: str
    tempSaveFlag: bool
    finishedStep: int
    notApplyItems: list[Any]
    jobType: str
    otherSpecify: str
    workExperience: list[WorkExperienceItem]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetWorkInfoData":
        we_raw = d.get("workExperience") or []
        return GetWorkInfoData(
            applyid=d.get("applyid", ""),
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            finishedStep=int(d.get("finishedStep", 0) or 0),
            notApplyItems=d.get("notApplyItems") or [],
            jobType=d.get("jobType", ""),
            otherSpecify=d.get("otherSpecify", ""),
            workExperience=[WorkExperienceItem.from_dict(x) for x in we_raw],
        )


@dataclass(slots=True)
class GetWorkInfoResponseWrapper:
    Data: Optional[GetWorkInfoData]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetWorkInfoResponseWrapper":
        data = d.get("Data")
        return GetWorkInfoResponseWrapper(
            Data=GetWorkInfoData.from_dict(data) if isinstance(data, dict) else None
        )


@dataclass(slots=True)
class GetWorkInfoResponse:
    Response: Optional[GetWorkInfoResponseWrapper]
    raw: dict[str, Any]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetWorkInfoResponse":
        resp = d.get("Response")
        return GetWorkInfoResponse(
            Response=(
                GetWorkInfoResponseWrapper.from_dict(resp)
                if isinstance(resp, dict)
                else None
            ),
            raw=d,
        )

    @property
    def data(self) -> Optional[GetWorkInfoData]:
        return self.Response.Data if self.Response and self.Response.Data else None
 