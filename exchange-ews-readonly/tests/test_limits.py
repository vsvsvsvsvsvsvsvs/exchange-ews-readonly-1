import pytest

from exchange_ews_readonly.config import Limits
from exchange_ews_readonly.errors import ConfigError
from exchange_ews_readonly.guards import clamp_list_limit, clamp_preview_chars, clamp_search_days


def test_default_limits_are_valid() -> None:
    limits = Limits()
    assert limits.list_default == 10
    assert limits.list_max == 50
    assert limits.search_days_default == 7
    assert limits.search_days_max == 30
    assert limits.preview_default == 500
    assert limits.preview_max == 1000


def test_list_limit_defaults_and_caps() -> None:
    assert clamp_list_limit(None) == 10
    assert clamp_list_limit(5) == 5
    assert clamp_list_limit(999) == 50


def test_search_days_defaults_and_caps() -> None:
    assert clamp_search_days(None) == 7
    assert clamp_search_days(2) == 2
    assert clamp_search_days(365) == 30


def test_preview_defaults_and_caps() -> None:
    assert clamp_preview_chars(None) == 500
    assert clamp_preview_chars(120) == 120
    assert clamp_preview_chars(5000) == 1000


@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_values_rejected(value: int) -> None:
    with pytest.raises(ValueError, match="must be > 0"):
        clamp_list_limit(value)
    with pytest.raises(ValueError, match="must be > 0"):
        clamp_search_days(value)
    with pytest.raises(ValueError, match="must be > 0"):
        clamp_preview_chars(value)


def test_limits_default_cannot_exceed_max() -> None:
    with pytest.raises(ConfigError, match="list default cannot exceed max"):
        Limits(list_default=51, list_max=50)


def test_limits_max_must_be_positive() -> None:
    with pytest.raises(ConfigError, match="preview max must be > 0"):
        Limits(preview_max=0)
