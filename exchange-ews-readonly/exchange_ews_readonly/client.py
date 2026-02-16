from __future__ import annotations

from .config import AuthType, Settings


class EwsConnectionError(RuntimeError):
    """Raised when EWS connection cannot be established safely."""


def build_account(settings: Settings) -> object:
    """
    Build a read-only-capable EWS account connection for on-prem Exchange.

    Notes:
    - Uses autodiscover=False by design.
    - Supports NTLM (default) and BASIC auth only.
    - Does not perform or expose any mailbox write operation.
    """
    try:
        from exchangelib import Account, BASIC, Configuration, Credentials, DELEGATE, NTLM
        from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
    except Exception as exc:  # pragma: no cover - environment dependent
        raise EwsConnectionError(
            "Failed to import exchangelib runtime dependencies"
        ) from exc

    try:
        credentials = Credentials(
            username=settings.username,
            password=settings.password,
        )

        auth_type = NTLM if settings.auth_type == AuthType.NTLM else BASIC

        # Global exchangelib protocol options.
        BaseProtocol.TIMEOUT = settings.timeout_seconds
        if not settings.verify_tls:
            BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        config = Configuration(
            server=settings.server,
            credentials=credentials,
            auth_type=auth_type,
        )

        account = Account(
            primary_smtp_address=settings.email,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        return account
    except Exception as exc:  # pragma: no cover - requires live EWS endpoint
        # Intentionally do not include username/password/token in error details.
        raise EwsConnectionError(
            "Failed to create EWS account connection. "
            "Check server/auth/TLS settings and mailbox permissions."
        ) from exc
