import subprocess
from typing import Tuple

from app.models.SubprocessResponse import SubprocessResponse


def _get_response(r: subprocess.CompletedProcess) -> Tuple[str, str, int]:
    # print(f"\t\tDEBUG::r={r}")
    out = r.stdout.decode("utf-8")
    err = r.stderr.decode("utf-8")
    code = r.returncode
    return (out, err, code)


def _op(args: list[str], capture: bool = False) -> SubprocessResponse:
    r = subprocess.run(args, capture_output=capture)
    (out, err, code) = _get_response(r)
    return SubprocessResponse(output=out, error=err, return_code=code)


def _op_json(args: list[str]) -> SubprocessResponse:
    args.append("--format=json")
    return _op(args=args, capture=True)


def op_create_vault(vault: str) -> SubprocessResponse:
    return _op_json(["op", "vault", "create", vault])


def op_whoami() -> SubprocessResponse:
    return _op_json(["op", "whoami"])
