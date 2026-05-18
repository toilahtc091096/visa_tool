from dataclasses import dataclass, field
from typing import Any


@dataclass
class StayInfo:
    sort: int = 1
    stayCity: str = ""
    stayCounty: str = ""
    travelAddr: str = ""
    arrivalDate: str = ""
    leaveDate: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "StayInfo":
        return StayInfo(
            sort=int(d.get("sort", 1) or 1),
            stayCity=d.get("stayCity", "") or "",
            stayCounty=d.get("stayCounty", "") or "",
            travelAddr=d.get("travelAddr", "") or "",
            arrivalDate=d.get("arrivalDate", "") or "",
            leaveDate=d.get("leaveDate", "") or "",
        )


@dataclass
class TravelInfoProfile:
    finishedStep: int
    embassy: str
    tempSaveFlag: bool
    userId: str
    leaveCity: str
    leaveCounty: str
    leaveDate: str
    leaveVehicleType: str
    disposableFunds: str
    disposableFundsCurrency: str
    emergencyCity: str
    emergencyContactFamilyName: str
    emergencyContactFirstName: str
    emergencyContactMiddlename: str
    emergencyCountry: str
    emergencyCounty: str
    emergencyEmail: str
    emergencyPhoneNumber: str
    emergencyProvince: str
    emergencyRelation: str
    emergencyStreetAddr: str
    emergencyZipCode: str
    payForTravel: str
    payForTravelAddr: str
    payForTravelCountry: str
    payForTravelEmail: str
    payForTravelName: str
    payForTravelOrganizationName: str
    payForTravelPhoneNumber: str
    payForTravelRelation: str
    havePeersFlag: bool
    invitationNumber: str
    inviteCity: str
    inviteCounty: str
    inviteEmail: str
    inviteName: str
    invitePhoneNumber: str
    inviteProvince: str
    inviteRelation: str
    inviteZipCode: str
    sponsorCity: str
    sponsorCountry: str
    sponsorCounty: str
    sponsorEmail: str
    sponsorName: str
    sponsorPhoneNumber: str
    sponsorProvince: str
    sponsorRelation: str
    sponsorType: str
    sponsorZipCode: str
    arrivalVehicleType: str
    arrivalCity: str
    arrivalCounty: str
    stayCity: str
    stayCounty: str
    travelAddr: str
    applyid: str
    arrivalDate: str
    lang: str

    travelCompanion: list[Any] = field(default_factory=list)
    notApplyItems: list[Any] = field(default_factory=list)
    stayInfo: list[StayInfo] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "TravelInfoProfile":
        return TravelInfoProfile(
            finishedStep=int(d.get("finishedStep", 0) or 0),
            embassy=d.get("embassy", "") or "",
            tempSaveFlag=bool(d.get("tempSaveFlag", False)),
            userId=d.get("userId", "") or "",
            leaveCity=d.get("leaveCity", "") or "",
            leaveCounty=d.get("leaveCounty", "") or "",
            leaveDate=d.get("leaveDate", "") or "",
            leaveVehicleType=d.get("leaveVehicleType", "") or "",
            disposableFunds=d.get("disposableFunds", "") or "",
            disposableFundsCurrency=d.get("disposableFundsCurrency", "") or "",
            emergencyCity=d.get("emergencyCity", "") or "",
            emergencyContactFamilyName=d.get("emergencyContactFamilyName", "") or "",
            emergencyContactFirstName=d.get("emergencyContactFirstName", "") or "",
            emergencyContactMiddlename=d.get("emergencyContactMiddlename", "") or "",
            emergencyCountry=d.get("emergencyCountry", "") or "",
            emergencyCounty=d.get("emergencyCounty", "") or "",
            emergencyEmail=d.get("emergencyEmail", "") or "",
            emergencyPhoneNumber=d.get("emergencyPhoneNumber", "") or "",
            emergencyProvince=d.get("emergencyProvince", "") or "",
            emergencyRelation=d.get("emergencyRelation", "") or "",
            emergencyStreetAddr=d.get("emergencyStreetAddr", "") or "",
            emergencyZipCode=d.get("emergencyZipCode", "") or "",
            payForTravel=d.get("payForTravel", "") or "",
            payForTravelAddr=d.get("payForTravelAddr", "") or "",
            payForTravelCountry=d.get("payForTravelCountry", "") or "",
            payForTravelEmail=d.get("payForTravelEmail", "") or "",
            payForTravelName=d.get("payForTravelName", "") or "",
            payForTravelOrganizationName=d.get("payForTravelOrganizationName", "") or "",
            payForTravelPhoneNumber=d.get("payForTravelPhoneNumber", "") or "",
            payForTravelRelation=d.get("payForTravelRelation", "") or "",
            havePeersFlag=bool(d.get("havePeersFlag", False)),
            invitationNumber=d.get("invitationNumber", "") or "",
            inviteCity=d.get("inviteCity", "") or "",
            inviteCounty=d.get("inviteCounty", "") or "",
            inviteEmail=d.get("inviteEmail", "") or "",
            inviteName=d.get("inviteName", "") or "",
            invitePhoneNumber=d.get("invitePhoneNumber", "") or "",
            inviteProvince=d.get("inviteProvince", "") or "",
            inviteRelation=d.get("inviteRelation", "") or "",
            inviteZipCode=d.get("inviteZipCode", "") or "",
            sponsorCity=d.get("sponsorCity", "") or "",
            sponsorCountry=d.get("sponsorCountry", "") or "",
            sponsorCounty=d.get("sponsorCounty", "") or "",
            sponsorEmail=d.get("sponsorEmail", "") or "",
            sponsorName=d.get("sponsorName", "") or "",
            sponsorPhoneNumber=d.get("sponsorPhoneNumber", "") or "",
            sponsorProvince=d.get("sponsorProvince", "") or "",
            sponsorRelation=d.get("sponsorRelation", "") or "",
            sponsorType=d.get("sponsorType", "") or "",
            sponsorZipCode=d.get("sponsorZipCode", "") or "",
            arrivalVehicleType=d.get("arrivalVehicleType", "") or "",
            arrivalCity=d.get("arrivalCity", "") or "",
            arrivalCounty=d.get("arrivalCounty", "") or "",
            stayCity=d.get("stayCity", "") or "",
            stayCounty=d.get("stayCounty", "") or "",
            travelAddr=d.get("travelAddr", "") or "",
            applyid=d.get("applyid", "") or "",
            arrivalDate=d.get("arrivalDate", "") or "",
            lang=d.get("lang", "") or "",
            travelCompanion=list(d.get("travelCompanion") or []),
            notApplyItems=list(d.get("notApplyItems") or []),
            stayInfo=[
                StayInfo.from_dict(item) for item in (d.get("stayInfo") or [])
            ],
        )
