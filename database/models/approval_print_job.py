from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ApprovalPrintJob:
    han_code: str
    status: str = "not_print"
    source_email: str = ""
    message_id: str = ""
    subject: str = ""
    attachment_paths: list[str] = field(default_factory=list)
    application_form_path: str = ""
    attempt_count: int = 0
    last_error: str = ""
    printed_at: datetime | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ApprovalPrintJob":
        return ApprovalPrintJob(
            id=data.get("id"),
            han_code=str(data.get("han_code", "") or ""),
            status=str(data.get("status", "not_print") or "not_print"),
            source_email=str(data.get("source_email", "") or ""),
            message_id=str(data.get("message_id", "") or ""),
            subject=str(data.get("subject", "") or ""),
            attachment_paths=list(data.get("attachment_paths") or []),
            application_form_path=str(data.get("application_form_path", "") or ""),
            attempt_count=int(data.get("attempt_count", 0) or 0),
            last_error=str(data.get("last_error", "") or ""),
            printed_at=data.get("printed_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
