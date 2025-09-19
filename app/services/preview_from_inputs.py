from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.services.list_vaults import get_existing_vault_index, normalize_vault_name
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
    - Annotates each planned name with [EXISTS] if it already exists, else [NEW].
    """
    scan = load_all_inputs(base_dir=base_dir)

    if scan.fatal_errors:
        print("FATAL:")
        for e in scan.fatal_errors:
            print(f"  - {e}")
        return

    # Bubble up file-level warnings/errors first
    for files in (scan.prefix_files, scan.suffix_files):
        for f in files:
            for w in f.warnings:
                print(f"[WARN][{f.batch_name}] {w}")
            for e in f.errors:
                print(f"[ERR ][{f.batch_name}] {e}")

    projects_by_batch = _collect_projects_by_batch(scan)
    roles_by_batch = _collect_roles_by_batch(scan)

    batches_with_prefix_only = sorted(set(projects_by_batch) - set(roles_by_batch))
    batches_with_suffix_only = sorted(set(roles_by_batch) - set(projects_by_batch))
    batches_ready = sorted(set(projects_by_batch) & set(roles_by_batch))

    for b in batches_with_prefix_only:
        print(f"[WARN][{b}] Skipping: prefixes present but no matching *-vault-suffixes.txt")
    for b in batches_with_suffix_only:
        print(f"[WARN][{b}] Skipping: suffixes present but no matching *-vault-prefixes.txt")

    if not batches_ready:
        print("No batches with both prefixes and suffixes. Nothing to preview.")
        return

    # Fetch existing vaults once (not fatal if it fails)
    existing_by_name_norm = {}
    existing_names_norm = set()
    try:
        existing_by_name_norm, existing_names_norm = get_existing_vault_index()
        print(f"\n[INFO] Loaded {len(existing_names_norm)} existing vault name(s) for duplicate checks.")
    except Exception as e:
        print(f"\n[WARN] Could not list existing vaults; duplicate check disabled: {e}")

    print("\n=== PREVIEW: planned vault names ===")
    total_batches = 0
    total_vaults = 0
    total_exists = 0
    total_new = 0

    for batch in batches_ready:
        projects = projects_by_batch.get(batch, [])
        roles = roles_by_batch.get(batch, [])
        n = len(projects) * len(roles)
        total_batches += 1
        total_vaults += n

        batch_exists = 0
        batch_new = 0

        print(f"\n[{batch}] {len(projects)} prefixes × {len(roles)} suffixes = {n} vault(s)")
        for p in projects:
            for r in roles:
                vault_name = f"{p}{VAULT_NAME_JOINER}{r}"
                if existing_names_norm:
                    norm = normalize_vault_name(vault_name)
                    if norm in existing_names_norm:
                        # Include id if we have it
                        suffix = ""
                        existing = existing_by_name_norm.get(norm)
                        if existing and getattr(existing, "id", None):
                            suffix = f" (id={existing.id})"
                        print(f"  - [EXISTS] {vault_name}{suffix}")
                        batch_exists += 1
                        continue
                print(f"  - [NEW]    {vault_name}")
                batch_new += 1

        total_exists += batch_exists
        total_new += batch_new
        print(f"  -> Batch summary: NEW={batch_new}, EXISTS={batch_exists}, TOTAL={batch_new + batch_exists}")

    print("\n=== SUMMARY ===")
    print(f"Batches ready: {total_batches}")
    print(f"Total planned vaults: {total_vaults}")
    print(f"Total NEW: {total_new}")
    print(f"Total EXISTS: {total_exists}")