from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class VisaRegistration:
    first_applyid: str | None
    full_name: str
    passport_number: str
    visa_type: str = ""
    status: str = "draft"
    payload: dict[str, Any] = field(default_factory=dict)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "VisaRegistration":
        return VisaRegistration(
            id=data.get("id"),
            first_applyid=data.get("first_applyid"),
            full_name=data.get("full_name", "") or "",
            passport_number=data.get("passport_number", "") or "",
            visa_type=data.get("visa_type", "") or "",
            status=data.get("status", "draft") or "draft",
            payload=dict(data.get("payload") or {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
