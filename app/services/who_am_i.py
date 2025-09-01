import sys

from app.models.ServiceAccountWhoamiResponse import ServiceAccountWhoamiResponse
from app.models.SubprocessResponse import OpStatus
from app.services.run_command import op_whoami


def _print(s: str):
    print(f"\tUUID: {s}")


# Get the User UUID of the person running the script.
# This is required for other parts of the script.
def get_my_uuid() -> str:
    _print("Ensuring you're signed into 1Password and obtaining your User ID.")
    # r = subprocess.run(["op", "whoami", "--format=json"], capture_output=True)
    r = op_whoami()

    # Catch error and kill process
    if r.status == OpStatus.FAILURE:
        sys.exit(
            "ERR: Unable to get your UUID. Make sure you are signed into the"
            + f"1Password CLI. Error: {r.error}"
        )

    try:
        validated = ServiceAccountWhoamiResponse.model_validate(r.formatted_output)
    except Exception:
        sys.exit(
            "ERR: whoami returned non-error response but output did not match expected result"
        )

    user_uuid: str = validated.user_uuid
    _print(f"Obtained User ID: {user_uuid}")
    return user_uuid
