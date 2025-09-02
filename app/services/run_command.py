import subprocess
from typing import Tuple

from app.models.SubprocessResponse import SubprocessResponse


def _get_response(r: subprocess.CompletedProcess) -> Tuple[str, str, int]:
    out: str = r.stdout.decode("utf-8")
    err: str = r.stderr.decode("utf-8")
    code: int = r.returncode
    return (out, err, code)


def _op(args: list[str]) -> SubprocessResponse:
    r = subprocess.run(args, capture_output=True)
    (out, err, code) = _get_response(r)
    return SubprocessResponse(
        command=" ".join(args), output=out, error=err, return_code=code
    )


def _op_json(args: list[str]) -> SubprocessResponse:
    args.append("--format=json")
    return _op(args=args)


def op_create_vault(vault: str) -> SubprocessResponse:
    return _op_json(["op", "vault", "create", vault])


def op_whoami() -> SubprocessResponse:
    return _op_json(["op", "whoami"])


def op_delete_vault(identifier: str) -> SubprocessResponse:
    return _op(["op", "vault", "delete", identifier])


def op_list_vaults() -> SubprocessResponse:
    return _op_json(["op", "vault", "list"])
