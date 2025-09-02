from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from app.models.DeleteRunReceipt import (
    DeleteRunReceipt,
    VaultDeleteFailure,
    VaultDeleteSuccess,
)
from app.models.RunReceipt import VaultSuccess  # structure in rollback.jsonl
from app.services.delete_vaults_with_retries import try_delete_vault
from app.services.who_am_i import try_get_uuid

OUTPUT_BASE_DIR = Path("output") / "runs"
DELETE_RECEIPT_NAME = "delete_last_run-receipt.json"
ROLLBACK_FILENAME = "rollback.jsonl"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _list_run_dirs() -> list[Path]:
    if not OUTPUT_BASE_DIR.exists():
        return []
    return sorted(
        [p for p in OUTPUT_BASE_DIR.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _find_last_rollback() -> Optional[Path]:
    for run_dir in _list_run_dirs():
        rollback = run_dir / ROLLBACK_FILENAME
        if rollback.exists() and rollback.is_file() and rollback.stat().st_size > 0:
            return run_dir
    return None


def _resolve_run_dir(run_id: Optional[str]) -> Path:
    if run_id:
        # first check if the directory exists
        run_dir = OUTPUT_BASE_DIR / run_id
        if not run_dir.exists() or not run_dir.is_dir():
            raise RuntimeError(f"Run id not found: {run_id}")

        # then check the file exists and is not-empty
        rb = run_dir / ROLLBACK_FILENAME
        if not rb.exists() or rb.stat().st_size == 0:
            raise RuntimeError(f"No rollback.jsonl (or empty) in run {run_id}")

        # the provided run_id was valid, return the Path
        return run_dir

    # no run_id provided (or was empty), use the last run_id
    latest = _find_last_rollback()
    if not latest:
        raise RuntimeError(
            "No run with a non-empty rollback.jsonl was found in output/runs/"
        )
    return latest


def _read_rollback(rb_path: Path) -> list[VaultSuccess]:
    results: list[VaultSuccess] = []
    with rb_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            s = raw.strip()
            if not s:
                continue
            try:
                data = json.loads(s)
                results.append(VaultSuccess.model_validate(data))
            except (json.JSONDecodeError, ValidationError) as e:
                # Skip malformed lines; deletion continues
                print(f"[SKIP] rollback line {line_no}: {e}")
                continue
    return results


# def delete_last_run() -> Path:
def delete_last_run(run_id: Optional[str] = None, dry_run: bool = False) -> Path:
    """
    Deletes all vaults listed in the latest run's rollback.jsonl.
    If run_id is None, picks the latest run. If dry_run, no deletions are performed.
    Returns the path to the created delete receipt.
    """
    actor_uuid = try_get_uuid()
    started_at = _now()

    # run_dir = _find_latest_run_with_rollback()
    # rollback_path = run_dir / ROLLBACK_FILENAME
    # run_id = run_dir.name
    run_dir = _resolve_run_dir(run_id)
    rollback_path = run_dir / ROLLBACK_FILENAME
    run_id_resolved = run_dir.name

    entries = _read_rollback(rollback_path)
    print(f"DELETE-LAST-RUN: Found {len(entries)} rollback entries in {rollback_path}")
    if dry_run:
        print("DELETE-LAST-RUN: DRY RUN (no deletions will occur)")

    planned: list[VaultDeleteSuccess] = []
    successes: list[VaultDeleteSuccess] = []
    failures: list[VaultDeleteFailure] = []

    for entry in entries:
        identifier = entry.vault_id or entry.vault_name  # prefer ID if present
        # pre-instantiate this record, may need for dry-run OR real-deal
        record = VaultDeleteSuccess(
            vault_id=entry.vault_id,
            vault_name=entry.vault_name,
            batch_name=entry.batch_name,
            project=entry.project,
        )
        if dry_run:
            planned.append(record)
            print(f"[DRY] would delete {identifier}")
            continue

        try:
            try_delete_vault(identifier)
            successes.append(record)
            print(f"[DEL OK] {identifier}")
        except Exception as e:
            failures.append(
                VaultDeleteFailure(
                    vault_id=entry.vault_id,
                    vault_name=entry.vault_name,
                    batch_name=entry.batch_name,
                    project=entry.project,
                    error=str(e),
                )
            )
            print(f"[DEL ERR] {identifier} -> {e}")

    finished_at = _now()
    receipt = DeleteRunReceipt(
        run_id_deleted=run_id_resolved,
        source_rollback_file=str(rollback_path),
        actor_uuid=actor_uuid,
        started_at=started_at,
        finished_at=finished_at,
        successes=successes,
        failures=failures,
    )

    out_path = run_dir / DELETE_RECEIPT_NAME
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(receipt.model_dump(), fh, indent=2, ensure_ascii=False)

    print(f"\nDelete complete. Receipt: {out_path}")
    return out_path
