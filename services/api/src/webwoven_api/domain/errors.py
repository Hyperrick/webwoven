"""Errors raised by deterministic domain rules."""


class DomainError(ValueError):
    """A command violates a game rule."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NotFoundError(LookupError):
    """A requested domain object does not exist."""


class ForbiddenError(PermissionError):
    """The current guest cannot access a domain object."""


class StaleStateError(RuntimeError):
    """A versioned command targets an older session snapshot."""

    def __init__(self, current_version: int) -> None:
        super().__init__("Session state changed; refresh and retry.")
        self.current_version = current_version
