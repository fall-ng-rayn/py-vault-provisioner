# app/services/exc.py
from __future__ import annotations


class VaultCreationError(Exception):
    """Base class for vault creation errors."""


class RateLimitedError(VaultCreationError):
    def __init__(
        self, message: str = "Rate limited", retry_after_minutes: int | None = None
    ):
        super().__init__(message)
        self.retry_after_minutes = retry_after_minutes


class CommandFailureError(VaultCreationError):
    def __init__(self, command: str, return_code: int, stderr: str | None):
        msg = f"op command ({command}) failed (return_code={return_code}, {'err=' + stderr if stderr else ''})"
        super().__init__(msg)
        self.return_code = return_code
        self.stderr = stderr


class OutputParseError(VaultCreationError):
    """`op` reported success, but output could not be parsed/validated."""

    pass


class UnknownStatusError(VaultCreationError):
    """Unexpected OpStatus (bug or new status)."""

    pass
