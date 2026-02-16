from datetime import datetime, timezone

import pytest

from exchange_ews_readonly.config import Limits, Settings
from exchange_ews_readonly.errors import MessageNotFoundError, ReadOnlyViolationError
from exchange_ews_readonly.service import EwsReadonlyService


class _FakeMailbox:
    def __init__(self, email_address: str) -> None:
        self.email_address = email_address


class _FakeItem:
    def __init__(self, item_id: str, subject: str, sender: str, body: str) -> None:
        self.id = item_id
        self.subject = subject
        self.sender = _FakeMailbox(sender)
        self.text_body = body
        self.body = body
        self.datetime_received = datetime(2026, 2, 16, tzinfo=timezone.utc)
        self.to_recipients = [_FakeMailbox("user@example.local")]
        self.cc_recipients = []


class _BrokenItem:
    def __init__(self) -> None:
        self.id = None
        self.subject = None
        self.sender = None
        self.text_body = None
        self.body = None
        self.datetime_received = None
        self.to_recipients = None
        self.cc_recipients = None


class _FakeInbox:
    def __init__(self, items: list[_FakeItem]) -> None:
        self._items = items

    def all(self) -> "_FakeInbox":
        return self

    def order_by(self, _field: str) -> "_FakeInbox":
        return self

    def filter(self, **_kwargs: object) -> "_FakeInbox":
        return self

    def get(self, id: str) -> _FakeItem:
        for item in self._items:
            if item.id == id:
                return item
        raise LookupError(id)

    def __getitem__(self, slc: slice) -> list[_FakeItem]:
        return self._items[slc]


class _FakeAccount:
    def __init__(self) -> None:
        self.inbox = _FakeInbox(
            [
                _FakeItem("1", "Invoice", "sender@example.local", "Body one"),
                _FakeItem("2", "Reminder", "sender2@example.local", "Body two"),
            ]
        )


class _BrokenAccount:
    def __init__(self) -> None:
        self.inbox = _FakeInbox([_BrokenItem()])


def _settings() -> Settings:
    return Settings(
        server="mail.example.local",
        email="user@example.local",
        username="EXAMPLE\\user",
        password="secret",
        limits=Limits(),
    )


def test_health_calls_read_only_guard_first(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def _guard(action: str) -> None:
        called.append(action)

    monkeypatch.setattr("exchange_ews_readonly.service.assert_read_only", _guard)
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())

    result = service.health()

    assert called == ["health"]
    assert result.status == "ok"


def test_list_messages_calls_read_only_guard_first(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def _guard(action: str) -> None:
        called.append(action)

    monkeypatch.setattr("exchange_ews_readonly.service.assert_read_only", _guard)
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())

    items = service.list_messages(limit=10, preview=200)

    assert called == ["list"]
    assert len(items) == 2


def test_get_message_calls_read_only_guard_first(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def _guard(action: str) -> None:
        called.append(action)

    monkeypatch.setattr("exchange_ews_readonly.service.assert_read_only", _guard)
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())

    message = service.get_message("1", preview=100)

    assert called == ["get"]
    assert message.id == "1"


def test_search_messages_calls_read_only_guard_first(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def _guard(action: str) -> None:
        called.append(action)

    monkeypatch.setattr("exchange_ews_readonly.service.assert_read_only", _guard)
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())

    result = service.search_messages(query="invoice", days=7, limit=10, preview=100)

    assert called == ["search"]
    assert len(result) == 1


def test_list_messages_handles_empty_or_broken_fields() -> None:
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _BrokenAccount())
    items = service.list_messages()

    assert len(items) == 1
    assert items[0].id == ""
    assert items[0].subject == ""
    assert items[0].sender == ""
    assert items[0].datetime_received == ""
    assert items[0].preview == ""


def test_get_message_trims_preview() -> None:
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())
    detail = service.get_message("1", preview=10)
    assert detail.body_preview.endswith("...")
    assert len(detail.body_preview) == 10


def test_search_messages_respects_result_limit() -> None:
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())
    result = service.search_messages(query="", limit=1)
    assert len(result) == 1


def test_get_message_not_found() -> None:
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())
    with pytest.raises(MessageNotFoundError, match="Message not found"):
        service.get_message("missing-id")


def test_service_blocks_unknown_action_via_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_action: str) -> None:
        raise ReadOnlyViolationError()

    monkeypatch.setattr("exchange_ews_readonly.service.assert_read_only", _raise)
    service = EwsReadonlyService(settings=_settings(), account_factory=lambda _: _FakeAccount())

    with pytest.raises(ReadOnlyViolationError):
        service.health()
