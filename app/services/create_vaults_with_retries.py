import time
from typing import Optional

from app.config.settings import settings
from app.models.CreateVaultResponse import CreateVaultResponse
from app.models.SubprocessResponse import OpStatus
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
    _print(f"Attempting to create vault: {vault}")
    _print(f"max-retries={settings.maxRetries}")
    _print("output-location=output/create")

    attempts = 0
    max_attempts = settings.maxRetries if settings.shouldRetry else 1
    while attempts < max_attempts:
        _print("Running op command...")
        sr = op_create_vault(vault)

        if sr.status == OpStatus.RATE_LIMITED:
            _print(f"`op create vault {vault}` rate-limited: retrying after sleep.")
            _sleep_minutes(minutes=10)

        elif sr.status == OpStatus.FAILURE:
            _print_oneline(
                [
                    f"`op create vault {vault}` failed:"
                    f"return-code={sr.return_code},"
                    f"error={sr.error}"
                ]
            )

        elif sr.status == OpStatus.SUCCESS:
            try:
                validated = CreateVaultResponse.model_validate(sr.formatted_output)
                _print("Vault created sucessfully!")
                if settings.shouldBuffer:
                    _sleep_seconds(seconds=2)
                return validated
            except Exception as e:
                _print("could not interpret vault creation output: " + str(e))

        else:
            _print(
                "something went wrong, vault creation status could not be determined."
                "return code was " + str(sr.return_code)
            )
            _sleep_seconds(seconds=5)

        # finally, increment counter
        attempts += 1
