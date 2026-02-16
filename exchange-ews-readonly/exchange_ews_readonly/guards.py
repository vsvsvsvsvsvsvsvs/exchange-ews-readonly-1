from __future__ import annotations

from .errors import ReadOnlyViolationError

ALLOWED_ACTIONS = {
    "health",
    "list",
    "get",
    "search",
}


def normalize_action(action: str) -> str:
    return action.strip().lower().replace("_", "-")


def ensure_action_allowed(action: str) -> None:
    normalized = normalize_action(action)
    if normalized not in ALLOWED_ACTIONS:
        raise ReadOnlyViolationError()


def assert_read_only(action: str) -> None:
    ensure_action_allowed(action)


def ensure_read_only(operation: str) -> None:
    # Backward-compatible alias used by service layer.
    if normalize_action(operation) not in ALLOWED_ACTIONS:
        raise ReadOnlyViolationError()


def clamp_list_limit(value: int | None, default: int = 10, maximum: int = 50) -> int:
    return _clamp_positive(value=value, default=default, maximum=maximum, label="list limit")


def clamp_search_days(value: int | None, default: int = 7, maximum: int = 30) -> int:
    return _clamp_positive(value=value, default=default, maximum=maximum, label="search days")


def clamp_preview_chars(value: int | None, default: int = 500, maximum: int = 1000) -> int:
    return _clamp_positive(value=value, default=default, maximum=maximum, label="preview")


def _clamp_positive(value: int | None, default: int, maximum: int, label: str) -> int:
    if value is None:
        return default
    if value <= 0:
        raise ValueError(f"{label} must be > 0")
    return min(value, maximum)
