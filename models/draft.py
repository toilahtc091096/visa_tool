from dataclasses import dataclass
from typing import Any, Optional

from constants import DEFAULT_EMBASSY


@dataclass
class GetDraftListBody:
    embassy: str = DEFAULT_EMBASSY
    PageNumber: int = 1
    PageSize: int = 10


@dataclass
class DraftItem:
    name: str
    applyDate: str
    applyid: str
    embassy: str
    visaType: Optional[str] = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DraftItem":
        return DraftItem(
            name=d.get("name", ""),
            applyDate=d.get("applyDate", ""),
            applyid=d.get("applyid", ""),
            embassy=d.get("embassy", ""),
            visaType=d.get("visaType"),
        )


@dataclass
class DraftData:
    pageNo: str
    pageSize: str
    total: str
    list: list[DraftItem]

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DraftData":
        items = [DraftItem.from_dict(x) for x in (d.get("list") or [])]
        return DraftData(
            pageNo=str(d.get("pageNo", "")),
            pageSize=str(d.get("pageSize", "")),
            total=str(d.get("total", "")),
            list=items,
        )


@dataclass
class DraftResponse:
    Data: DraftData

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DraftResponse":
        return DraftResponse(Data=DraftData.from_dict(d.get("Data") or {}))


@dataclass
class GetDraftListResult:
    Response: DraftResponse

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "GetDraftListResult":
        return GetDraftListResult(
            Response=DraftResponse.from_dict(d.get("Response") or {})
        )


def has_name(result: GetDraftListResult, inputname: str) -> bool:
    target = (inputname or "").strip().casefold()
    return any(
        (it.name or "").strip().casefold() == target
        for it in result.Response.Data.list
    )
 