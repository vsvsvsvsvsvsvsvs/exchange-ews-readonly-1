from __future__ import annotations

import logging
import re
from typing import Iterable


class RedactSecretsFilter(logging.Filter):
    _KEY_VALUE_PATTERNS = (
        re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"),
        re.compile(r"(?i)\b(token|access_token|refresh_token|api_key|secret)\s*[:=]\s*([^\s,;]+)"),
        re.compile(r"(?i)\b(auth|authorization)\s*[:=]\s*([^\s,;]+)"),
    )

    _HEADER_PATTERNS = (
        re.compile(r"(?i)(authorization:\s*)([^\r\n]+)"),
        re.compile(r"(?i)(x-auth-token:\s*)([^\r\n]+)"),
    )

    def __init__(self, secrets: Iterable[str] | None = None) -> None:
        super().__init__()
        self._secrets = [value for value in (secrets or []) if value]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        sanitized = self._sanitize(message)
        if sanitized != message:
            record.msg = sanitized
            record.args = ()
        return True

    def _sanitize(self, message: str) -> str:
        sanitized = message
        for secret in self._secrets:
            sanitized = sanitized.replace(secret, "***")

        for pattern in self._KEY_VALUE_PATTERNS:
            sanitized = pattern.sub(lambda match: f"{match.group(1)}=***", sanitized)

        for pattern in self._HEADER_PATTERNS:
            sanitized = pattern.sub(lambda match: f"{match.group(1)}***", sanitized)

        return sanitized


def configure_logging(level: str = "INFO", secrets: Iterable[str] | None = None) -> logging.Logger:
    logger = logging.getLogger("exchange_ews_readonly")
    logger.handlers.clear()
    logger.setLevel(level.upper())
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(RedactSecretsFilter(secrets=secrets))

    logger.addHandler(handler)
    return logger
