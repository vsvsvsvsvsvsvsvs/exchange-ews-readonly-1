import pytest
from cryptography.fernet import Fernet

from exchange_ews_readonly.config import AuthType, Settings
from exchange_ews_readonly.errors import ConfigError


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXCHANGE_EWS_SERVER", "mail.example.local")
    monkeypatch.setenv("EXCHANGE_EWS_EMAIL", "user@example.local")
    monkeypatch.setenv("EXCHANGE_EWS_USERNAME", "EXAMPLE\\user")

    key = Fernet.generate_key()
    token = Fernet(key).encrypt(b"super-secret")
    monkeypatch.setenv("EXCHANGE_EWS_CRYPTO_KEY", key.decode("utf-8"))
    monkeypatch.setenv("EXCHANGE_EWS_PASSWORD_ENC", token.decode("utf-8"))
    monkeypatch.delenv("EXCHANGE_EWS_ALLOW_PLAINTEXT_PASSWORD", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_PASSWORD", raising=False)


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("EXCHANGE_EWS_AUTH_TYPE", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_VERIFY_TLS", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_TIMEOUT_SEC", raising=False)

    settings = Settings.from_env()

    assert settings.auth_type == AuthType.NTLM
    assert settings.timeout_seconds == 30
    assert settings.verify_tls is True
    assert settings.password == "super-secret"


def test_auth_type_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("EXCHANGE_EWS_AUTH_TYPE", "BASIC")

    settings = Settings.from_env()
    assert settings.auth_type == AuthType.BASIC


def test_username_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("EXCHANGE_EWS_USERNAME", raising=False)

    settings = Settings.from_env()
    assert settings.username == "user@example.local"


def test_plaintext_password_fallback_requires_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXCHANGE_EWS_SERVER", "mail.example.local")
    monkeypatch.setenv("EXCHANGE_EWS_EMAIL", "user@example.local")
    monkeypatch.setenv("EXCHANGE_EWS_PASSWORD", "legacy-secret")
    monkeypatch.delenv("EXCHANGE_EWS_PASSWORD_ENC", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_CRYPTO_KEY", raising=False)
    monkeypatch.setenv("EXCHANGE_EWS_ALLOW_PLAINTEXT_PASSWORD", "true")

    settings = Settings.from_env()
    assert settings.password == "legacy-secret"


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("EXCHANGE_EWS_SERVER", "", "Missing required environment variable"),
        ("EXCHANGE_EWS_EMAIL", "invalid-email", "must be a valid email address"),
        ("EXCHANGE_EWS_SERVER", "https://mail.example.local", "must be a host name only"),
        ("EXCHANGE_EWS_AUTH_TYPE", "KERBEROS", "must be one of"),
        ("EXCHANGE_EWS_VERIFY_TLS", "maybe", "must be boolean"),
        ("EXCHANGE_EWS_TIMEOUT_SEC", "abc", "must be an integer"),
        ("EXCHANGE_EWS_TIMEOUT_SEC", "0", "must be between 1 and 300"),
    ],
)
def test_invalid_env_values_raise_clear_errors(
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: str,
    message: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv(key, value)

    with pytest.raises(ConfigError, match=message):
        Settings.from_env()


def test_missing_encrypted_password_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXCHANGE_EWS_SERVER", "mail.example.local")
    monkeypatch.setenv("EXCHANGE_EWS_EMAIL", "user@example.local")
    monkeypatch.delenv("EXCHANGE_EWS_PASSWORD_ENC", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_CRYPTO_KEY", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_PASSWORD", raising=False)
    monkeypatch.delenv("EXCHANGE_EWS_ALLOW_PLAINTEXT_PASSWORD", raising=False)

    with pytest.raises(ConfigError, match="EXCHANGE_EWS_PASSWORD_ENC"):
        Settings.from_env()


def test_invalid_crypto_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXCHANGE_EWS_SERVER", "mail.example.local")
    monkeypatch.setenv("EXCHANGE_EWS_EMAIL", "user@example.local")
    monkeypatch.setenv("EXCHANGE_EWS_CRYPTO_KEY", "invalid-key")
    monkeypatch.setenv("EXCHANGE_EWS_PASSWORD_ENC", "invalid-token")

    with pytest.raises(ConfigError, match="EXCHANGE_EWS_CRYPTO_KEY is invalid"):
        Settings.from_env()
