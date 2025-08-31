import json
import subprocess
import time
from typing import Optional, Tuple

from lib.models import CreateVaultResponse, OpStatus
from lib.run_command import create_one_vault
from lib.settings import settings


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


def _get_response(r: subprocess.CompletedProcess) -> Tuple[str, str, str]:
    out = r.stdout.decode("utf-8")
    err = r.stderr.decode("utf-8")
    code = str(r.returncode)
    return (out, err, code)


def create_vault(vault: str) -> Optional[CreateVaultResponse]:
    _print(f"Attempting to create vault: {vault}")
    _print(f"max-retries={settings.maxRetries}")
    _print("output-location=output/create")

    attempts = 0
    max_attempts = settings.maxRetries if settings.shouldRetry else 1
    while attempts < max_attempts:
        _print("Running op command...")
        sr = create_one_vault(vault)

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
                jr = json.loads(sr.output)
                validated = CreateVaultResponse.model_validate(jr)
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

    return None
