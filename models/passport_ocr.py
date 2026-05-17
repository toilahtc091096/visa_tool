from dataclasses import dataclass, field
from typing import Any


@dataclass
class PassportOCRData:
    dateOfBirth: str | None = None
    dateOfExpiration: str | None = None
    fileId: str | None = None
    issuingCountry: str | None = None
    name: str | None = None
    nationality: str | None = None
    passportFamilyName: str | None = None
    passportFirstName: str | None = None
    passportNumber: str | None = None
    sex: str | None = None
    warn: list[Any] = field(default_factory=list)


@dataclass
class PassportOCRError:
    Code: str | None = None
    Message: str | None = None


@dataclass
class PassportOCRResponse:
    Data: PassportOCRData | None = None
    Error: PassportOCRError | None = None


@dataclass
class PassportOCRResult:
    Response: PassportOCRResponse


def passport_ocr_result_from_dict(d: dict[str, Any]) -> PassportOCRResult:
    resp = (d or {}).get("Response") or {}

    err = resp.get("Error")
    error_obj = None
    if isinstance(err, dict):
        error_obj = PassportOCRError(
            Code=err.get("Code"),
            Message=err.get("Message"),
        )

    data = resp.get("Data")
    data_obj = None
    if isinstance(data, dict):
        data_obj = PassportOCRData(
            dateOfBirth=data.get("dateOfBirth"),
            dateOfExpiration=data.get("dateOfExpiration"),
            fileId=data.get("fileId"),
            issuingCountry=data.get("issuingCountry"),
            name=data.get("name"),
            nationality=data.get("nationality"),
            passportFamilyName=data.get("passportFamilyName"),
            passportFirstName=data.get("passportFirstName"),
            passportNumber=data.get("passportNumber"),
            sex=data.get("sex"),
            warn=data.get("warn") or [],
        )

    return PassportOCRResult(
        Response=PassportOCRResponse(Data=data_obj, Error=error_obj)
    )
