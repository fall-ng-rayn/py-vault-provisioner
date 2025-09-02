import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config.settings import settings
from app.models.PacificDatetime import to_pacific
from app.models.RunReceipt import (
    RunReceipt,
    VaultFailure,
    VaultSuccess,
)
from app.services.create_vaults_with_retries import try_create_vault
from app.services.exc import VaultCreationError
from app.services.list_vaults import get_existing_vault_index, normalize_vault_name
from app.services.load_project_inputs import load_all_inputs

VAULT_NAME_JOINER = getattr(settings, "vaultNameJoiner", " - ")
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


def _collect_projects_by_batch(scan) -> dict[str, list[str]]:
    """
    Collapse all prefix files by batch_name -> unique, sorted project list.
    """
    buckets: dict[str, set[str]] = {}
    for f in scan.prefix_files:
        if f.projects:
            b = buckets.setdefault(f.batch_name, set())
            b.update(f.projects)
    return {k: sorted(v) for k, v in buckets.items()}


def _collect_roles_by_batch(scan) -> dict[str, list[str]]:
    """
    Collapse all suffix files by batch_name -> unique, sorted role list.
    """
    buckets: dict[str, set[str]] = {}
    for f in scan.suffix_files:
        if f.roles:
            b = buckets.setdefault(f.batch_name, set())
            b.update(f.roles)
    return {k: sorted(v) for k, v in buckets.items()}


def run_from_inputs(uuid: str, base_dir: Optional[Path] = None) -> Path:
    """
    Executes a batch run from ./input/*-vault-prefixes.txt + *-vault-suffixes.txt.
    Produces:
      - receipt JSON  (per-run summary)
      - rollback.jsonl (one line per successful vault creation)
    Skips any batch_name that is missing either side (prefixes or suffixes), with a warning.
    """
    now = _now()
    started_at = now
    run_id = _new_run_id(now)
    run_dir = _ensure_run_dir(run_id)
    rollback_path = run_dir / "rollback.jsonl"

    scan = load_all_inputs(base_dir=base_dir)

    # Aggregate file-level warnings/errors for the final receipt
    warnings: list[str] = []
    errors: list[str] = []
    input_files: list[str] = []

    for files in [scan.prefix_files, scan.suffix_files]:
        for f in files:
            input_files.append(f.path.name)
            warnings.extend(f"[{f.batch_name}] {w}" for w in f.warnings)
            errors.extend(f"[{f.batch_name}] {e}" for e in f.errors)

    successes: list[VaultSuccess] = []
    failures: list[VaultFailure] = []

    try:
        existing_by_name_norm, existing_names_norm = get_existing_vault_index()
    except Exception as e:
        # Not fatal—proceed, but surface the limitation
        warnings.append(
            f"[global] Could not list existing vaults; duplicate check disabled: {e}"
        )
        existing_by_name_norm, existing_names_norm = {}, set()

    if scan.fatal_errors:
        errors.extend(scan.fatal_errors)
    else:
        # Build cross-product per batch_name, but only when both sides present
        projects_by_batch = _collect_projects_by_batch(scan)
        roles_by_batch = _collect_roles_by_batch(scan)

        batches_with_prefix_only = sorted(
            set(projects_by_batch.keys()) - set(roles_by_batch.keys())
        )
        batches_with_suffix_only = sorted(
            set(roles_by_batch.keys()) - set(projects_by_batch.keys())
        )
        for b in batches_with_prefix_only:
            warnings.append(
                f"[{b}] Skipping batch: found prefixes but no *-vault-suffixes.txt."
            )
        for b in batches_with_suffix_only:
            warnings.append(
                f"[{b}] Skipping batch: found suffixes but no *-vault-prefixes.txt."
            )

        batches_ready = sorted(
            set(projects_by_batch.keys()) & set(roles_by_batch.keys())
        )

        for batch_name in batches_ready:
            projects = projects_by_batch.get(batch_name, [])
            roles = roles_by_batch.get(batch_name, [])
            # defensive (shouldn't be empty if batch in batches_ready)
            if not projects or not roles:
                warnings.append(
                    f"[{batch_name}] Skipping batch: empty projects or roles AFTER validation (this shouldn't happen)."
                )
                continue

            for project in projects:
                for role in roles:
                    vault_name = f"{project}{VAULT_NAME_JOINER}{role}"
                    norm = normalize_vault_name(vault_name)

                    # check to see if our generated vault name already exists
                    if norm in existing_names_norm:
                        msg = "already exists"
                        msg_verbose = msg
                        existing = existing_by_name_norm.get(norm)
                        if existing and getattr(existing, "id", None):
                            msg_verbose += f" (id={existing.id})"
                        failures.append(
                            VaultFailure(
                                batch_name=batch_name,
                                project=project,
                                vault_name=vault_name,
                                error=msg_verbose,
                            )
                        )
                        print(f"[SKIP] {vault_name} (batch={batch_name}) -> {msg}")
                        continue

                    try:
                        resp = try_create_vault(vault_name)
                        vault_id = _extract_vault_id(resp)

                        success = VaultSuccess(
                            batch_name=batch_name,
                            project=project,
                            vault_name=vault_name,
                            vault_id=vault_id,
                        )
                        successes.append(success)

                        with rollback_path.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps(success.model_dump()) + os.linesep)

                        print(f"[OK] {vault_name} (batch={batch_name}), id={vault_id}")

                    except VaultCreationError as e:
                        msg = str(e)
                        failures.append(
                            VaultFailure(
                                batch_name=batch_name,
                                project=project,
                                vault_name=vault_name,
                                error=msg,
                            )
                        )
                        print(f"[ERR] {vault_name} (batch={batch_name}) -> {msg}")

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
