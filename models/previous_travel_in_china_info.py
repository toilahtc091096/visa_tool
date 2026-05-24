from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreviousTravelInChinaInfo:
    entryDate: str = ""
    exitDate: str = ""
    city: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "PreviousTravelInChinaInfo":
        return PreviousTravelInChinaInfo(
            entryDate=d.get("entryDate", "") or "",
            exitDate=d.get("exitDate", "") or "",
            city=d.get("city", "") or "",
        )


@dataclass
class ChinaVisaProfile:
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

    previousTravelInChinaInfos: list[PreviousTravelInChinaInfo] = field(default_factory=list)

    provideChinaVisaDetailFlag: str

    residenceLicenseNumber: str

    visaNumber: str
    visaType: str

    notApplyItems: list[Any] = field(default_factory=list)

    applyid: str

    firstApplyChinaVisaFlag: bool

    lang: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ChinaVisaProfile":
        return ChinaVisaProfile(
            applyCountry=d.get("applyCountry", "") or "",

            finishedStep=int(d.get("finishedStep", 0) or 0),

            embassy=d.get("embassy", "") or "",

            tempSaveFlag=bool(d.get("tempSaveFlag", False)),

            userId=d.get("userId", "") or "",

            arrivedChinaFlag=bool(d.get("arrivedChinaFlag", False)),

            chinaResidenceLicenseFlag=bool(
                d.get("chinaResidenceLicenseFlag", False)
            ),

            collectFingerprintCountry=d.get(
                "collectFingerprintCountry", ""
            ) or "",

            collectFingerprintDate=d.get(
                "collectFingerprintDate", ""
            ) or "",

            collectFingerprintFlag=bool(
                d.get("collectFingerprintFlag", False)
            ),

            collectFingerprintPlace=d.get(
                "collectFingerprintPlace", ""
            ) or "",

            haveChinaVisaFlag=bool(
                d.get("haveChinaVisaFlag", False)
            ),

            haveOtherVisaFlag=bool(
                d.get("haveOtherVisaFlag", False)
            ),

            issueDate=d.get("issueDate", "") or "",

            issuePlace=d.get("issuePlace", "") or "",

            visitedOtherCountryFlag=bool(
                d.get("visitedOtherCountryFlag", False)
            ),

            lostChinaVisaDate=d.get(
                "lostChinaVisaDate", ""
            ) or "",

            lostChinaVisaFlag=d.get(
                "lostChinaVisaFlag", ""
            ) or "",

            lostChinaVisaNumber=d.get(
                "lostChinaVisaNumber", ""
            ) or "",

            lostChinaVisaPlace=d.get(
                "lostChinaVisaPlace", ""
            ) or "",

            otherCountries=d.get("otherCountries", "") or "",

            otherVisas=d.get("otherVisas", "") or "",

            previousTravelInChinaInfos=[
                PreviousTravelInChinaInfo.from_dict(item)
                for item in (d.get("previousTravelInChinaInfos") or [])
            ],

            provideChinaVisaDetailFlag=d.get(
                "provideChinaVisaDetailFlag", ""
            ) or "",

            residenceLicenseNumber=d.get(
                "residenceLicenseNumber", ""
            ) or "",

            visaNumber=d.get("visaNumber", "") or "",

            visaType=d.get("visaType", "") or "",

            notApplyItems=list(d.get("notApplyItems") or []),

            applyid=d.get("applyid", "") or "",

            firstApplyChinaVisaFlag=bool(
                d.get("firstApplyChinaVisaFlag", False)
            ),

            lang=d.get("lang", "") or "",
        )