# models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass(slots=True)
class LoginData:
    uid: str
    token: str
    refreshToken: Optional[str]
    tmpSecret: str
    userId: str
    userEmail: str
    centerId: str
    guid: str
    embassyId: str
    plt: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LoginData":
        return cls(
            uid=d.get("uid", ""),
            token=d.get("token", ""),
            refreshToken=d.get("refreshToken"),
            tmpSecret=d.get("tmpSecret", ""),
            userId=d.get("userId", ""),
            userEmail=d.get("userEmail", ""),
            centerId=d.get("centerId", ""),
            guid=d.get("guid", ""),
            embassyId=d.get("embassyId", ""),
            plt=d.get("plt", ""),
        )


@dataclass(slots=True)
class LoginApiResponse:
    msg: str
    code: int
    data: Optional[LoginData]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LoginApiResponse":
        raw_data = d.get("data")
        return cls(
            msg=d.get("msg", ""),
            code=int(d.get("code", 0) or 0),
            data=LoginData.from_dict(raw_data) if isinstance(raw_data, dict) else None,
        )