from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreviousTravelInfoProfile:
    applyCountry: str
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str
    arrivedChinaFlag: bool
    chinaResidenceLicenseFlag: bool
    collectFingerprintCountry: str
    collectFingerprintDate: str
    collectFingerprintFlag: bool
    collectFingerprintPlace: str
    haveChinaVisaFlag: bool
    haveOtherVisaFlag: bool
    issueDate: str
    issuePlace: str
    visitedOtherCountryFlag: bool
    lostChinaVisaDate: str
    lostChinaVisaFlag: str
    lostChinaVisaNumber: str
    lostChinaVisaPlace: str
    otherCountries: str
    otherVisas: str
    provideChinaVisaDetailFlag: str
    residenceLicenseNumber: str
    visaNumber: str
    visaType: str
    applyid: str
    firstApplyChinaVisaFlag: bool
    lang: str

    notApplyItems: list[Any] = field(default_factory=list)
    previousTravelInChinaInfos: list[Any] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "PreviousTravelInfoProfile":
        return PreviousTravelInfoProfile(
            applyCountry=d.get("applyCountry", "") or "",
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",
            arrivedChinaFlag=bool(d.get("arrivedChinaFlag", False)),
            chinaResidenceLicenseFlag=d.get("chinaResidenceLicenseFlag", False) or False,
            collectFingerprintCountry=d.get("collectFingerprintCountry", "") or "",
            collectFingerprintDate=d.get("collectFingerprintDate", "") or "",
            collectFingerprintFlag=d.get("collectFingerprintFlag", False) or False,
            collectFingerprintPlace=d.get("collectFingerprintPlace", "") or "",
            haveChinaVisaFlag=bool(d.get("haveChinaVisaFlag", False)),
            haveOtherVisaFlag=bool(d.get("haveOtherVisaFlag", False)),
            issueDate=d.get("issueDate", "") or "",
            issuePlace=d.get("issuePlace", "") or "",
            visitedOtherCountryFlag=bool(d.get("visitedOtherCountryFlag", False)),
            lostChinaVisaDate=d.get("lostChinaVisaDate", "") or "",
            lostChinaVisaFlag=d.get("lostChinaVisaFlag", "") or "",
            lostChinaVisaNumber=d.get("lostChinaVisaNumber", "") or "",
            lostChinaVisaPlace=d.get("lostChinaVisaPlace", "") or "",
            otherCountries=d.get("otherCountries", "") or "",
            otherVisas=d.get("otherVisas", "") or "",
            provideChinaVisaDetailFlag=d.get("provideChinaVisaDetailFlag", "") or "",
            residenceLicenseNumber=d.get("residenceLicenseNumber", "") or "",
            visaNumber=d.get("visaNumber", "") or "",
            visaType=d.get("visaType", "") or "",
            applyid=d.get("applyid", "") or "",
            firstApplyChinaVisaFlag=bool(d.get("firstApplyChinaVisaFlag", False)),
            lang=d.get("lang", "") or "",
            notApplyItems=list(d.get("notApplyItems") or []),
            previousTravelInChinaInfos=list(d.get("previousTravelInChinaInfos") or []),
        )
