# models/online_application_list.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class OnlineApplicationRow:
    createBy: str
    createTime: str
    updateBy: str
    updateTime: str
    remark: Optional[str]

    id: int
    embassy: str
    applyid: str
    passport: str
    nationalityCountry: str

    applyDate: str
    applyDateLocal: str
    birthday: str

    visaType: str
    serviceType: str
    applyVisaValidity: str
    applyMaxStayDays: str
    applyVisaTimes: str

    companionNumber: int
    email: str
    amount: float
    currency: str

    paymentType: str
    paymentStatus: str
    paymentTime: Optional[str]

    applyStatus: str
    operateTimestamp: str

    yyNo: Optional[str]
    appointmentDate: Optional[str]
    appointmentTime: Optional[str]

    rejectReason: Optional[str]

    cancelStatus: Optional[str]
    cancelCode: Optional[str]
    cancelMessage: Optional[str]

    createTimeLocal: Optional[str]
    updateTimeLocal: Optional[str]

    certificate: Optional[str]
    consularUid: str
    centerId: str
    alFormId: str

    handleMethod: str
    retrievePassport: str

    postCompany: Optional[str]
    postTrack: Optional[str]
    postAddress: Optional[str]
    postPostcode: Optional[str]

    vipService: Any
    vipServiceList: Any

    paymentMethod: str
    passportType: str
    expirationDate: str
    status: str

    cityNameEn: Optional[str]
    submitTime: Optional[str]
    submitTimeLocal: Optional[str]

    bizOlAlFormFee: Any
    bizOlPay: Any
    logId: Any
    paymentResponse: Any
    chargeVisaFee: Any
    chargeServiceFee: Any

    paytime: Optional[str]
    payamount: Optional[str]
    paycurrency: Optional[str]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "OnlineApplicationRow":
        return OnlineApplicationRow(
            createBy=d.get("createBy", ""),
            createTime=d.get("createTime", ""),
            updateBy=d.get("updateBy", ""),
            updateTime=d.get("updateTime", ""),
            remark=d.get("remark"),

            id=int(d.get("id", 0) or 0),
            embassy=d.get("embassy", ""),
            applyid=d.get("applyid", ""),
            passport=d.get("passport", ""),
            nationalityCountry=d.get("nationalityCountry", ""),

            applyDate=d.get("applyDate", ""),
            applyDateLocal=d.get("applyDateLocal", ""),
            birthday=d.get("birthday", ""),

            visaType=d.get("visaType", ""),
            serviceType=d.get("serviceType", ""),
            applyVisaValidity=str(d.get("applyVisaValidity", "")),
            applyMaxStayDays=str(d.get("applyMaxStayDays", "")),
            applyVisaTimes=d.get("applyVisaTimes", ""),

            companionNumber=int(d.get("companionNumber", 0) or 0),
            email=d.get("email", ""),
            amount=float(d.get("amount", 0) or 0),
            currency=d.get("currency", ""),

            paymentType=str(d.get("paymentType", "")),
            paymentStatus=str(d.get("paymentStatus", "")),
            paymentTime=d.get("paymentTime"),

            applyStatus=d.get("applyStatus", ""),
            operateTimestamp=d.get("operateTimestamp", ""),

            yyNo=d.get("yyNo"),
            appointmentDate=d.get("appointmentDate"),
            appointmentTime=d.get("appointmentTime"),

            rejectReason=d.get("rejectReason"),

            cancelStatus=d.get("cancelStatus"),
            cancelCode=d.get("cancelCode"),
            cancelMessage=d.get("cancelMessage"),

            createTimeLocal=d.get("createTimeLocal"),
            updateTimeLocal=d.get("updateTimeLocal"),

            certificate=d.get("certificate"),
            consularUid=d.get("consularUid", ""),
            centerId=d.get("centerId", ""),
            alFormId=d.get("alFormId", ""),

            handleMethod=d.get("handleMethod", ""),
            retrievePassport=d.get("retrievePassport", ""),

            postCompany=d.get("postCompany"),
            postTrack=d.get("postTrack"),
            postAddress=d.get("postAddress"),
            postPostcode=d.get("postPostcode"),

            vipService=d.get("vipService"),
            vipServiceList=d.get("vipServiceList"),

            paymentMethod=str(d.get("paymentMethod", "")),
            passportType=d.get("passportType", ""),
            expirationDate=d.get("expirationDate", ""),
            status=str(d.get("status", "")),

            cityNameEn=d.get("cityNameEn"),
            submitTime=d.get("submitTime"),
            submitTimeLocal=d.get("submitTimeLocal"),

            bizOlAlFormFee=d.get("bizOlAlFormFee"),
            bizOlPay=d.get("bizOlPay"),
            logId=d.get("logId"),
            paymentResponse=d.get("paymentResponse"),
            chargeVisaFee=d.get("chargeVisaFee"),
            chargeServiceFee=d.get("chargeServiceFee"),

            paytime=d.get("paytime"),
            payamount=d.get("payamount"),
            paycurrency=d.get("paycurrency"),
        )


@dataclass(slots=True)
class OnlineApplicationListResponse:
    total: int
    rows: list[OnlineApplicationRow]
    code: int
    msg: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "OnlineApplicationListResponse":
        rows_raw = d.get("rows") or []
        return OnlineApplicationListResponse(
            total=int(d.get("total", 0) or 0),
            rows=[OnlineApplicationRow.from_dict(x) for x in rows_raw],
            code=int(d.get("code", 0) or 0),
            msg=d.get("msg", ""),
        )