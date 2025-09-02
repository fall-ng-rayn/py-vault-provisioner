import time
from typing import Optional

from app.config.settings import settings
from app.models.CreateVaultResponse import CreateVaultResponse
from app.models.SubprocessResponse import OpStatus
from app.services.exc import (
    CommandFailureError,
    OutputParseError,
    RateLimitedError,
    UnknownStatusError,
    VaultCreationError,
)
from app.services.run_command import op_create_vault


def _print(s: str):
    print(f"\tCREATE: {s}")


def _print_oneline(s: list):
    print(f"\tCREATE: {' '.join(s)}")


def _sleep_seconds(seconds: int):
    _print(f"Sleeping for {seconds} sec...")
    time.sleep(seconds)


def _sleep_minutes(minutes: int):
    _print(f"Sleeping for {minutes} min...")
    time.sleep(minutes * 60)


def try_create_vault(vault: str) -> Optional[CreateVaultResponse]:
    """
    Create a vault named `vault`.
    - On success: returns CreateVaultResponse
    - On failure: raises VaultCreationError (subclass)
    """

    attempts = 0
    max_attempts = settings.maxRetries if settings.shouldRetry else 1
    last_error: Optional[VaultCreationError] = None

    while attempts < max_attempts:
        sr = op_create_vault(vault)

        if sr.status == OpStatus.RATE_LIMITED:
            last_error = RateLimitedError(
                message=f"`op create vault {vault}` rate-limited: retrying after sleep.",
                retry_after_minutes=settings.backoffMin,
            )
            _print("[NEW WARN] " + str(last_error))
            if attempts < max_attempts - 1:
                _sleep_minutes(minutes=settings.backoffMin)
                attempts += 1
                continue
            else:
                break

        elif sr.status == OpStatus.FAILURE:
            last_error = CommandFailureError(
                command="vault create", return_code=sr.return_code, stderr=sr.error
            )
            _print_oneline(
                [
                    "[NEW ERR]",
                    f"`op create vault {vault}` failed:",
                    f"return-code={sr.return_code},error={sr.error}",
                ]
            )
            break

        elif sr.status == OpStatus.SUCCESS:
            try:
                validated = CreateVaultResponse.model_validate(sr.formatted_output)
                _print("Vault created sucessfully!")
                if settings.shouldBuffer:
                    _sleep_seconds(seconds=settings.bufferSeconds)
                return validated
            except Exception as e:
                last_error = OutputParseError(
                    "could not interpret vault creation output: " + str(e)
                )
                _print(str(last_error))
                break

        else:
            last_error = UnknownStatusError(
                f"Unknown status {sr.status!r} (return_code={sr.return_code})"
            )
            _print(str(last_error))
            break

    # Out of attempts -> raise the last error we saw
    raise last_error or VaultCreationError("Vault creation failed for unknown reasons.")
