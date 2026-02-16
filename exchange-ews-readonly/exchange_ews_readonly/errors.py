READ_ONLY_VIOLATION_MESSAGE = "READ_ONLY_VIOLATION: write operations are disabled"


class ReadOnlyViolationError(RuntimeError):
    """Raised when any non-read-only action is attempted."""

    def __init__(self, message: str = READ_ONLY_VIOLATION_MESSAGE) -> None:
        super().__init__(message)


class ConfigError(ValueError):
    """Raised when required settings are invalid."""


class MessageNotFoundError(LookupError):
    """Raised when message lookup returns no result."""
