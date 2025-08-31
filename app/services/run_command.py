import subprocess
from typing import Tuple

from app.models.SubprocessResponse import SubprocessResponse


def _get_response(r: subprocess.CompletedProcess) -> Tuple[str, str, int]:
    out = r.stdout.decode("utf-8")
    err = r.stderr.decode("utf-8")
    code = r.returncode
    return (out, err, code)


def create_one_vault(vault: str) -> SubprocessResponse:
    args = ["op", "vault", "create", vault, "--format=json"]
    r = subprocess.run(args, capture_output=True)
    (out, err, code) = _get_response(r)
    return SubprocessResponse(output=out, error=err, return_code=code)
