from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from .client import build_account
from .config import Settings
from .errors import MessageNotFoundError
from .guards import assert_read_only, clamp_list_limit, clamp_preview_chars, clamp_search_days
from .models import HealthResult, MailDetail, MailSummary


class EwsReadonlyService:
    def __init__(
        self,
        settings: Settings,
        account_factory: Callable[[Settings], object] = build_account,
    ) -> None:
        self._settings = settings
        self._account_factory = account_factory
        self._account = None

    @property
    def account(self) -> object:
        if self._account is None:
            self._account = self._account_factory(self._settings)
        return self._account

    def health(self) -> HealthResult:
        assert_read_only("health")
        inbox_accessible = bool(list(self.account.inbox.all()[:1]))  # noqa: C401
        return HealthResult(
            status="ok",
            server=self._settings.server,
            email=self._settings.email,
            inbox_accessible=inbox_accessible,
        )

    def list_messages(self, limit: int | None = None, preview: int | None = None) -> list[MailSummary]:
        assert_read_only("list")
        list_limit = clamp_list_limit(limit, self._settings.limits.list_default, self._settings.limits.list_max)
        preview_size = clamp_preview_chars(
            preview,
            self._settings.limits.preview_default,
            self._settings.limits.preview_max,
        )
        items = self.account.inbox.all().order_by("-datetime_received")[:list_limit]
        return [self._to_summary(item, preview_size) for item in items]

    def get_message(self, message_id: str, preview: int | None = None) -> MailDetail:
        assert_read_only("get")
        preview_size = clamp_preview_chars(
            preview,
            self._settings.limits.preview_default,
            self._settings.limits.preview_max,
        )
        try:
            item = self.account.inbox.get(id=message_id)
        except Exception as exc:  # pragma: no cover - depends on EWS backend types
            raise MessageNotFoundError(f"Message not found: {message_id}") from exc
        return self._to_detail(item, preview_size)

    def search_messages(
        self,
        query: str,
        days: int | None = None,
        limit: int | None = None,
        preview: int | None = None,
    ) -> list[MailSummary]:
        assert_read_only("search")
        list_limit = clamp_list_limit(limit, self._settings.limits.list_default, self._settings.limits.list_max)
        days_limit = clamp_search_days(
            days,
            self._settings.limits.search_days_default,
            self._settings.limits.search_days_max,
        )
        preview_size = clamp_preview_chars(
            preview,
            self._settings.limits.preview_default,
            self._settings.limits.preview_max,
        )

        since = datetime.now(timezone.utc) - timedelta(days=days_limit)
        prefetch_size = min(list_limit * 5, self._settings.limits.list_max)
        items = self.account.inbox.filter(datetime_received__gte=since).order_by("-datetime_received")[:prefetch_size]

        needle = query.strip().lower()
        matched: list[object] = []
        for item in items:
            if not needle:
                matched.append(item)
            else:
                sender = _mailbox_to_str(getattr(item, "sender", None))
                haystack = " ".join(
                    [
                        (getattr(item, "subject", "") or ""),
                        sender,
                        _extract_body_text(item),
                    ]
                ).lower()
                if needle in haystack:
                    matched.append(item)

            if len(matched) >= list_limit:
                break

        return [self._to_summary(item, preview_size) for item in matched[:list_limit]]

    # Backward-compatible aliases for earlier CLI/service usage.
    def list(self, limit: int | None = None, preview: int | None = None) -> list[MailSummary]:
        assert_read_only("list")
        return self.list_messages(limit=limit, preview=preview)

    def get(self, message_id: str, preview: int | None = None) -> MailDetail:
        assert_read_only("get")
        return self.get_message(message_id=message_id, preview=preview)

    def search(
        self,
        query: str,
        days: int | None = None,
        limit: int | None = None,
        preview: int | None = None,
    ) -> list[MailSummary]:
        assert_read_only("search")
        return self.search_messages(query=query, days=days, limit=limit, preview=preview)

    def _to_summary(self, item: object, preview_size: int) -> MailSummary:
        return MailSummary(
            id=_text_or_empty(getattr(item, "id", "")),
            subject=(getattr(item, "subject", "") or ""),
            sender=_mailbox_to_str(getattr(item, "sender", None)),
            datetime_received=_to_iso(getattr(item, "datetime_received", None)),
            preview=_trim_text(_extract_body_text(item), preview_size),
        )

    def _to_detail(self, item: object, preview_size: int) -> MailDetail:
        return MailDetail(
            id=_text_or_empty(getattr(item, "id", "")),
            subject=(getattr(item, "subject", "") or ""),
            sender=_mailbox_to_str(getattr(item, "sender", None)),
            to_recipients=_recipient_list(getattr(item, "to_recipients", []) or []),
            cc_recipients=_recipient_list(getattr(item, "cc_recipients", []) or []),
            datetime_received=_to_iso(getattr(item, "datetime_received", None)),
            body_preview=_trim_text(_extract_body_text(item), preview_size),
        )


def _to_iso(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return ""


def _recipient_list(items: list[object]) -> list[str]:
    result: list[str] = []
    for item in items:
        value = _mailbox_to_str(item)
        if value:
            result.append(value)
    return result


def _mailbox_to_str(value: object) -> str:
    if value is None:
        return ""
    email_address = getattr(value, "email_address", None)
    if email_address:
        return str(email_address)
    return str(value)


def _extract_body_text(item: object) -> str:
    text_body = getattr(item, "text_body", None)
    if text_body:
        return str(text_body)
    body = getattr(item, "body", None)
    return str(body or "")


def _trim_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3] + "..."


def _text_or_empty(value: object) -> str:
    if value is None:
        return ""
    return str(value)
