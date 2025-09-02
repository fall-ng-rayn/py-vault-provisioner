from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.services.load_project_inputs import load_all_inputs

VAULT_NAME_JOINER = getattr(settings, "vaultNameJoiner", " - ")


def _collect_projects_by_batch(scan) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {}
    for f in scan.prefix_files:
        if f.projects:
            buckets.setdefault(f.batch_name, set()).update(f.projects)
    return {k: sorted(v) for k, v in buckets.items()}


def _collect_roles_by_batch(scan) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {}
    for f in scan.suffix_files:
        if f.roles:
            buckets.setdefault(f.batch_name, set()).update(f.roles)
    return {k: sorted(v) for k, v in buckets.items()}


def preview_from_inputs(base_dir: Optional[Path] = None) -> None:
    """
    Print a human-friendly preview of planned vault names without creating anything.
    - Skips batches missing either prefixes or suffixes (prints warnings).
    """
    scan = load_all_inputs(base_dir=base_dir)

    if scan.fatal_errors:
        print("FATAL:")
        for e in scan.fatal_errors:
            print(f"  - {e}")
        return

    total_batches = 0
    total_vaults = 0

    # Bubble up file-level warnings/errors first
    for f in scan.prefix_files:
        for w in f.warnings:
            print(f"[WARN][{f.batch_name}] {w}")
        for e in f.errors:
            print(f"[ERR ][{f.batch_name}] {e}")
    for f in scan.suffix_files:
        for w in f.warnings:
            print(f"[WARN][{f.batch_name}] {w}")
        for e in f.errors:
            print(f"[ERR ][{f.batch_name}] {e}")

    projects_by_batch = _collect_projects_by_batch(scan)
    roles_by_batch = _collect_roles_by_batch(scan)

    batches_with_prefix_only = sorted(
        set(projects_by_batch.keys()) - set(roles_by_batch.keys())
    )
    batches_with_suffix_only = sorted(
        set(roles_by_batch.keys()) - set(projects_by_batch.keys())
    )
    batches_ready = sorted(set(projects_by_batch.keys()) & set(roles_by_batch.keys()))

    for b in batches_with_prefix_only:
        print(
            f"[WARN][{b}] Skipping: prefixes present but no matching *-vault-suffixes.txt"
        )

    for b in batches_with_suffix_only:
        print(
            f"[WARN][{b}] Skipping: suffixes present but no matching *-vault-prefixes.txt"
        )

    if not batches_ready:
        print("No batches with both prefixes and suffixes. Nothing to preview.")
        return

    print("\n=== PREVIEW: planned vault names ===")
    for batch in batches_ready:
        projects = projects_by_batch.get(batch, [])
        roles = roles_by_batch.get(batch, [])
        n = len(projects) * len(roles)
        total_batches += 1
        total_vaults += n

        print(
            f"\n[{batch}] {len(projects)} prefixes × {len(roles)} suffixes = {n} vault(s)"
        )
        for p in projects:
            for r in roles:
                vault_name = f"{p}{VAULT_NAME_JOINER}{r}"
                print(f"  - {vault_name}")

    print("\n=== SUMMARY ===")
    print(f"Batches ready: {total_batches}")
    print(f"Total planned vaults: {total_vaults}")
