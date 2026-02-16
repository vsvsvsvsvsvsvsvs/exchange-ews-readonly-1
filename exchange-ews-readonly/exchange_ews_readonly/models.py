from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HealthResult:
    status: str
    server: str
    email: str
    inbox_accessible: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MailSummary:
    id: str
    subject: str
    sender: str
    datetime_received: str
    preview: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MailDetail:
    id: str
    subject: str
    sender: str
    to_recipients: list[str]
    cc_recipients: list[str]
    datetime_received: str
    body_preview: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
