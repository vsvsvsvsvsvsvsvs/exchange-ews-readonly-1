import pytest

from exchange_ews_readonly.errors import READ_ONLY_VIOLATION_MESSAGE, ReadOnlyViolationError
from exchange_ews_readonly.guards import ALLOWED_ACTIONS, assert_read_only, ensure_action_allowed, ensure_read_only


@pytest.mark.parametrize(
    "action",
    ["health", "list", "get", "search"],
)
def test_allowed_actions_are_whitelisted(action: str) -> None:
    assert action in ALLOWED_ACTIONS
    ensure_action_allowed(action)


@pytest.mark.parametrize(
    "action",
    [
        "send",
        "reply",
        "forward",
        "delete",
        "move",
        "copy",
        "mark",
        "mark-read",
        "mark-unread",
        "read",
        "unread",
        "update",
        "save",
        "create",
        "draft",
        "create-draft",
        "custom-action",
        "unknown",
        "HEALTHCHECK",
    ],
)
def test_non_whitelisted_actions_raise_read_only_violation(action: str) -> None:
    with pytest.raises(ReadOnlyViolationError, match=READ_ONLY_VIOLATION_MESSAGE):
        ensure_action_allowed(action)


def test_legacy_ensure_read_only_alias_blocks_unknown_action() -> None:
    with pytest.raises(ReadOnlyViolationError, match=READ_ONLY_VIOLATION_MESSAGE):
        ensure_read_only("anything-else")


def test_legacy_ensure_read_only_alias_allows_read_command() -> None:
    ensure_read_only("list")


def test_assert_read_only_blocks_unknown_action() -> None:
    with pytest.raises(ReadOnlyViolationError, match=READ_ONLY_VIOLATION_MESSAGE):
        assert_read_only("something-new")
