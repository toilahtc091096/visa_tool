from dataclasses import dataclass, field
from typing import Any


@dataclass
class EducationExperience:
    sort: str = ""
    beginDate: str = ""
    endDate: str = ""
    schoolName: str = ""
    schoolAddr: str = ""
    highestDegree: str = ""
    specialty: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "EducationExperience":
        return EducationExperience(
            sort=d.get("sort", "") or "",
            beginDate=d.get("beginDate", "") or "",
            endDate=d.get("endDate", "") or "",
            schoolName=d.get("schoolName", "") or "",
            schoolAddr=d.get("schoolAddr", "") or "",
            highestDegree=d.get("highestDegree", "") or "",
            specialty=d.get("specialty", "") or "",
        )


@dataclass
class EducationInfoProfile:
    applyCountry: str
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str
    language: str
    applyid: str
    lang: str

    notApplyItems: list[Any] = field(default_factory=list)
    educationExperience: list[EducationExperience] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "EducationInfoProfile":
        return EducationInfoProfile(
            applyCountry=d.get("applyCountry", "") or "",
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",
            language=d.get("language", "") or "",
            applyid=d.get("applyid", "") or "",
            lang=d.get("lang", "") or "",
            notApplyItems=list(d.get("notApplyItems") or []),
            educationExperience=[
                EducationExperience.from_dict(item)
                for item in (d.get("educationExperience") or [])
            ],
        )
