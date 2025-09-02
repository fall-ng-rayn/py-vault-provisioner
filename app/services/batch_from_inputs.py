import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config.settings import settings
from app.models.RunReceipt import (
    RunReceipt,
    VaultFailure,
    VaultSuccess,
    to_pacific,
)
from app.services.exc import VaultCreationError
from app.services.load_project_inputs import load_all_inputs

OUTPUT_BASE_DIR = Path("output") / "runs"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_run_id(now: Optional[datetime]) -> str:
    now = now or _now()
    if settings.usePacificTz:
        # e.g., 2025-09-01_16-47-00-0700
        timestamp = to_pacific(now).strftime("%Y-%m-%d_%H-%M-%S%z")
    else:
        # e.g. 2025-09-01_01-23-45Z_7f3a2c
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%SZ")
    random = secrets.token_hex(3)
    return f"{timestamp}_{random}"


def _ensure_run_dir(run_id: str) -> Path:
    run_dir = OUTPUT_BASE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _extract_vault_id(resp: Any) -> Optional[str]:
    """
    Best-effort extractor—supports dict- or object-like CreateVaultResponse.
    """
    try:
        # dict-ish
        if isinstance(resp, dict):
            return (
                resp.get("vault_id")
                or resp.get("id")
                or (resp.get("vault") or {}).get("id")
            )
        # object-ish
        for attr in ("vault_id", "id"):
            if hasattr(resp, attr):
                v = getattr(resp, attr)
                if v:
                    return str(v)
        # nested 'vault'
        vault = getattr(resp, "vault", None)
        if vault is not None:
            for attr in ("id", "vault_id"):
                if hasattr(vault, attr):
                    v = getattr(vault, attr)
                    if v:
                        return str(v)
    except Exception:
        pass
    return None


def run_from_inputs(uuid: str, base_dir: Optional[Path] = None) -> Path:
    """
    Executes a batch run from ./input/*.txt files.
    Returns the created run directory path with artifacts:
      - receipt.json
      - rollback.jsonl  (one line per successful creation)
    """
    now = _now()
    started_at = now
    run_id = _new_run_id(now)
    run_dir = _ensure_run_dir(run_id)
    rollback_path = run_dir / "rollback.jsonl"

    scan = load_all_inputs(base_dir=base_dir)

    # Aggregate file-level warnings/errors for the final receipt
    warnings = []
    errors = []
    input_files = []

    for f in scan.files:
        input_files.append(f.path.name)
        warnings.extend(f"[{f.batch_name}] {w}" for w in f.warnings)
        errors.extend(f"[{f.batch_name}] {e}" for e in f.errors)

    successes: list[VaultSuccess] = []
    failures: list[VaultFailure] = []

    if scan.fatal_errors:
        errors.extend(scan.fatal_errors)
    else:
        # Process each project line-by-line
        for f in scan.files:
            for project in f.projects:
                # TODO -----------------------------------------------
                # This will need to change, need to add another
                # for-loop around our role_names.txt results.
                # vault_name will become project+role_name
                # (or similar)
                vault_name = project  # vault name == project string
                try:
                    # TODO - TESTING -- revert later
                    # resp = try_create_vault(vault_name)
                    resp = {"id": secrets.token_hex(8)}  # MONKEYPATCH

                    vault_id = _extract_vault_id(resp)

                    # Record success
                    success = VaultSuccess(
                        batch_name=f.batch_name,
                        project=project,
                        vault_name=vault_name,
                        vault_id=vault_id,
                    )
                    successes.append(success)

                    # Create rollback file
                    with rollback_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(success.model_dump()) + os.linesep)

                    print(f"[OK] {vault_name} (batch={f.batch_name}), id={vault_id}")
                except VaultCreationError as e:
                    msg = str(e)
                    failures.append(
                        VaultFailure(
                            batch_name=f.batch_name,
                            project=project,
                            vault_name=vault_name,
                            error=msg,
                        )
                    )
                    print(f"[ERR] {vault_name} (batch={f.batch_name}) -> {msg}")
                # end-try-catch
            # end-for-f.projects
        # end-for-scan.files
    # end-else

    finished_at = _now()
    receipt = RunReceipt(
        run_id=run_id,
        actor_uuid=uuid,
        started_at=started_at,
        finished_at=finished_at,
        input_files=input_files,
        warnings=warnings,
        errors=errors,
        successes=successes,
        failures=failures,
    )

    receipt_filename = "batch_from_inputs-receipt.json"
    with (run_dir / receipt_filename).open("w", encoding="utf-8") as fh:
        json.dump(receipt.model_dump(), fh, indent=2, ensure_ascii=False)

    # Helpful, human-readable pointer
    to_stdout = [
        "Run Complete. Artifacts:",
        f" - {run_dir / receipt_filename}",
        f" - {rollback_path}",
    ]
    print("\n".join(to_stdout))

    return run_dir
