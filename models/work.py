from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkExperience:
    sort: str = ""
    beginDate: str = ""
    endDate: str = ""
    jobName: str = ""
    jobAddr: str = ""
    jobTel: str = ""
    jobPosition: str = ""
    jobDuty: str = ""
    supervisorName: str = ""
    supervisorTel: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "WorkExperience":
        return WorkExperience(
            sort=d.get("sort", "") or "",
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


@dataclass
class WorkInfoProfile:
    applyCountry: str
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str
    jobType: str
    otherSpecify: str
    d3: bool
    annualIncome: str
    currency: str
    applyid: str
    lang: str

    notApplyItems: list[Any] = field(default_factory=list)
    workExperience: list[WorkExperience] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "WorkInfoProfile":
        return WorkInfoProfile(
            applyCountry=d.get("applyCountry", "") or "",
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",
            jobType=d.get("jobType", "") or "",
            otherSpecify=d.get("otherSpecify", "") or "",
            d3=bool(d.get("d3", False)),
            annualIncome=d.get("annualIncome", "") or "",
            currency=d.get("currency", "") or "",
            applyid=d.get("applyid", "") or "",
            lang=d.get("lang", "") or "",
            notApplyItems=list(d.get("notApplyItems") or []),
            workExperience=[
                WorkExperience.from_dict(item)
                for item in (d.get("workExperience") or [])
            ],
        )
