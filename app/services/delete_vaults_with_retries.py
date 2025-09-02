# app/services/delete_vaults_with_retries.py
from __future__ import annotations

import time
from typing import Optional

from app.config.settings import settings
from app.models.SubprocessResponse import OpStatus
from app.services.exc import (
    CommandFailureError,
    RateLimitedError,
    UnknownStatusError,
    VaultCreationError,  # reuse types for rate limit / command failure
)
from app.services.run_command import op_delete_vault


def _print(s: str) -> None:
    print(f"\tDELETE: {s}")


def _sleep_seconds(seconds: int) -> None:
    _print(f"Sleeping for {seconds} sec...")
    time.sleep(seconds)


def _sleep_minutes(minutes: int) -> None:
    _print(f"Sleeping for {minutes} min...")
    time.sleep(minutes * 60)


def try_delete_vault(identifier: str) -> None:
    """
    Delete a vault by id or name.
    - On success: returns None
    - On failure: raises Exception (RateLimitedError, CommandFailureError, UnknownStatusError)
    """
    _print(f"Attempting to delete vault: {identifier!r}")
    attempts = 0
    max_attempts = settings.maxRetries if settings.shouldRetry else 1
    buffer_seconds = settings.bufferSeconds if settings.shouldBuffer else 0
    last_error: Optional[VaultCreationError] = None  # reuse base error class

    while attempts < max_attempts:
        sr = op_delete_vault(identifier)

        if sr.status == OpStatus.RATE_LIMITED:
            last_error = RateLimitedError(
                "`op vault delete` rate-limited.", retry_after_minutes=10
            )
            _print(str(last_error))
            if attempts < max_attempts - 1:
                _sleep_minutes(settings.backoffMin)
                attempts += 1
                continue
            break

        elif sr.status == OpStatus.FAILURE:
            last_error = CommandFailureError(
                command="vault delete", return_code=sr.return_code, stderr=sr.error
            )
            _print(str(last_error))
            break

        elif sr.status == OpStatus.SUCCESS:
            _print("Vault deleted successfully.")
            if settings.shouldBuffer:
                _sleep_seconds(buffer_seconds)
            return

        else:
            last_error = UnknownStatusError(
                f"Unknown status {sr.status!r} (return_code={sr.return_code})"
            )
            _print(str(last_error))
            break

    raise last_error or CommandFailureError(
        command="vault delete", return_code=-1, stderr="Unknown delete failure"
    )
