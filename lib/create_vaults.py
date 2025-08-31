import subprocess
import time
import json
from typing import Dict, Optional, Tuple

from lib.models import CreateVaultResponse

SLEEP_BETWEEN_CREATES: bool = True
CREATE_SLEEP_SEC: int = 10
RATE_LIMIT_BACKOFF_MIN: int = 10
MAX_RETRIES = 3
WITH_RETRIES: bool = False


def _print(s: str):
    print(f"\tCREATE: {s}")


def _sleep_minutes(minutes: int):
    time.sleep(minutes * 60)


def _get_response(r: subprocess.CompletedProcess) -> Tuple[str, str, str]:
    err = r.stderr.decode("utf-8")
    code = str(r.returncode)
    out = r.stdout.decode("utf-8")
    return (out, err, code)


def _try_once(vault: str) -> Dict[str, str]:
    _print("Attempting to create vault: " + vault)
    r = subprocess.run(
        ["op", "vault", "create", vault, "--format=json"],
        capture_output=True,
    )

    response = _get_response(r)
    (out, err, code) = response

    was_rate_limited = "rate-limited" in err
    if was_rate_limited:
        # Retry after backoff period
        minutes = RATE_LIMIT_BACKOFF_MIN
        _print(err)
        _print(f"Sleeping for {minutes} min...")
        _sleep_minutes(minutes)
        return {}

    elif code != "0" and not was_rate_limited:
        _print(f"Unable to create vault. Error: {err}")
        return {}

    _print("Vault creation successful!")
    if SLEEP_BETWEEN_CREATES:
        # Guard against rate-limit
        _print(f"Sleeping {CREATE_SLEEP_SEC} sec")
        time.sleep(CREATE_SLEEP_SEC)
    return json.loads(out)


def create_vault(vault: str) -> Optional[CreateVaultResponse]:
    _print(
        "Vault creation retry metadata: "
        + f"retries-enabled={WITH_RETRIES}, "
        + f"max-retries={MAX_RETRIES}"
    )
    response = _try_once(vault)
    try:
        return CreateVaultResponse.model_validate(response)
    except Exception as e:
        _print("could not interpret vault creation output: " + str(e))

    if not WITH_RETRIES:
        return None
    else:
        retries = 1
        while retries < MAX_RETRIES:
            response = _try_once(vault)
            if response:
                try:
                    return CreateVaultResponse.model_validate(response)
                except Exception as e:
                    _print("could not interpret vault creation output: " + str(e))
            retries += 1
    return None
