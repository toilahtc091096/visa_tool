from dataclasses import dataclass
from typing import Any


@dataclass
class UploadMaterialBody:
    filePath: str = ""
    fileName: str = ""
    categoryCode: str = ""
    materialCode: str = ""
    businessId: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "UploadMaterialBody":
        return UploadMaterialBody(
            filePath=d.get("filePath", "") or "",
            fileName=d.get("fileName", "") or "",
            categoryCode=d.get("categoryCode", "") or "",
            materialCode=d.get("materialCode", "") or "",
            businessId=d.get("businessId", "") or "",
        )