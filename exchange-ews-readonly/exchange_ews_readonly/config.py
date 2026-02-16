from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum

from .errors import ConfigError


class AuthType(str, Enum):
    NTLM = "NTLM"
    BASIC = "BASIC"


@dataclass(frozen=True)
class Limits:
    list_default: int = 10
    list_max: int = 50
    search_days_default: int = 7
    search_days_max: int = 30
    preview_default: int = 500
    preview_max: int = 1000

    def __post_init__(self) -> None:
        _validate_limit_pair("list", self.list_default, self.list_max)
        _validate_limit_pair("search days", self.search_days_default, self.search_days_max)
        _validate_limit_pair("preview", self.preview_default, self.preview_max)


@dataclass(frozen=True)
class Settings:
    server: str
    email: str
    username: str
    password: str = field(repr=False)
    auth_type: AuthType = AuthType.NTLM
    verify_tls: bool = True
    timeout_seconds: int = 30
    limits: Limits = field(default_factory=Limits)

    @classmethod
    def from_env(cls) -> "Settings":
        server = _read_server("EXCHANGE_EWS_SERVER")
        email = _read_email("EXCHANGE_EWS_EMAIL")
        username = _optional_env("EXCHANGE_EWS_USERNAME") or email
        password = _require_env("EXCHANGE_EWS_PASSWORD")

        raw_auth = os.getenv("EXCHANGE_EWS_AUTH_TYPE", AuthType.NTLM.value).strip().upper()
        auth_type = _read_auth_type(raw_auth)
        verify_tls = _read_bool("EXCHANGE_EWS_VERIFY_TLS", default=True)
        timeout_seconds = _read_int("EXCHANGE_EWS_TIMEOUT_SEC", default=30, minimum=1, maximum=300)

        return cls(
            server=server,
            email=email,
            username=username,
            password=password,
            auth_type=auth_type,
            verify_tls=verify_tls,
            timeout_seconds=timeout_seconds,
            limits=Limits(),
        )


def _read_server(name: str) -> str:
    value = _require_env(name)
    if "://" in value:
        raise ConfigError(f"{name} must be a host name only (without http/https scheme)")
    if "/" in value:
        raise ConfigError(f"{name} must not contain a URL path")
    return value


def _read_email(name: str) -> str:
    value = _require_env(name)
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ConfigError(f"{name} must be a valid email address")
    return value


def _read_auth_type(raw_auth: str) -> AuthType:
    try:
        return AuthType(raw_auth)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in AuthType)
        raise ConfigError(f"EXCHANGE_EWS_AUTH_TYPE must be one of: {allowed}") from exc


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def _optional_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be boolean: true/false")


def _read_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value < minimum or value > maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


def _validate_limit_pair(label: str, default: int, maximum: int) -> None:
    if default <= 0:
        raise ConfigError(f"{label} default must be > 0")
    if maximum <= 0:
        raise ConfigError(f"{label} max must be > 0")
    if default > maximum:
        raise ConfigError(f"{label} default cannot exceed max")
