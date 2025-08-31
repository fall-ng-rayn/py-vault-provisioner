import sys
import subprocess
import json


# Get the User UUID of the person running the script.
# This is required for other parts of the script.
def get_my_uuid(log: bool = False) -> str:
    def _print(s:str):
        if log:
            print(f"\tUUID: {s}")

    _print("Ensuring you're signed into 1Password and obtaining your User ID.")

    r = subprocess.run(["op", "whoami", "--format=json"], capture_output=True)

    # Catch error and kill process
    if r.returncode != 0:
        sys.exit(
            f"ERR: Unable to get your UUID. Make sure you are signed into the 1Password CLI. Error: {r.stderr.decode('utf-8')}"
        )

    user_uuid: str = json.loads(r.stdout)["user_uuid"]
    _print(f"Obtained User ID: {user_uuid}")
    return user_uuid
