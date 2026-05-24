from dataclasses import dataclass
from typing import Any


@dataclass
class ContactInfoProfile:
    applyCountry: str

    finishedStep: int

    embassy: str

    tempSaveFlag: bool

    userId: str

    agentFlag: bool

    agentName: str

    W2: str

    relationship: str

    agentAddr: str

    agentTel: str

    applyid: str

    lang: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ContactInfoProfile":
        return ContactInfoProfile(
            applyCountry=d.get("applyCountry", "") or "",

            finishedStep=int(d.get("finishedStep", 0) or 0),

            embassy=d.get("embassy", "") or "",

            tempSaveFlag=bool(d.get("tempSaveFlag", False)),

            userId=d.get("userId", "") or "",

            agentFlag=bool(d.get("agentFlag", False)),

            agentName=d.get("agentName", "") or "",

            W2=d.get("W2", "") or "",

            relationship=d.get("relationship", "") or "",

            agentAddr=d.get("agentAddr", "") or "",

            agentTel=d.get("agentTel", "") or "",

            applyid=d.get("applyid", "") or "",

            lang=d.get("lang", "") or "",
        )