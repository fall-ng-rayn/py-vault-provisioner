from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.services.list_vaults import canonical_vault_key, get_existing_vault_indexes, normalize_vault_name
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
    scan = load_all_inputs(base_dir=base_dir)
    if scan.fatal_errors:
        print("FATAL:")
        for e in scan.fatal_errors:
            print(f"  - {e}")
        return

    # surface file warnings/errors
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

    # indexes
    by_norm = {}
    norm_keys = set()
    by_canon = {}
    canon_keys = set()
    try:
        by_norm, norm_keys, by_canon, canon_keys = get_existing_vault_indexes()
        print(f"\n[INFO] Loaded {len(norm_keys)} existing vault(s) for exact & canonical checks.")
    except Exception as e:
        print(f"\n[WARN] Could not list existing vaults; duplicate checks disabled: {e}")

    print("\n=== PREVIEW: planned vault names ===")
    total_batches = total_vaults = total_exists = total_conflicts = total_new = 0

    for batch in batches_ready:
        projects = projects_by_batch.get(batch, [])
        roles = roles_by_batch.get(batch, [])
        n = len(projects) * len(roles)
        total_batches += 1
        total_vaults += n

        batch_exists = batch_conflicts = batch_new = 0
        print(f"\n[{batch}] {len(projects)} prefixes × {len(roles)} suffixes = {n} vault(s)")

        for p in projects:
            for r in roles:
                name = f"{p}{VAULT_NAME_JOINER}{r}"
                status = "[NEW]"
                suffix = ""

                if norm_keys:
                    nk = normalize_vault_name(name)
                    if nk in norm_keys:
                        status = "[EXISTS]"
                        v = by_norm.get(nk)
                        if v and getattr(v, "id", None):
                            suffix = f" (id={v.id})"
                        batch_exists += 1
                    else:
                        ck = canonical_vault_key(name)
                        if ck in canon_keys:
                            status = "[CONFLICT]"
                            # show one conflicting exemplar
                            arr = by_canon.get(ck) or []
                            if arr:
                                v = arr[0]
                                suffix = f" (conflicts with existing '{v.name}'" + (f", id={v.id}" if getattr(v, 'id', None) else "") + ")"
                            batch_conflicts += 1
                        else:
                            batch_new += 1
                else:
                    batch_new += 1

                print(f"  - {status} {name}{suffix}")

        total_exists += batch_exists
        total_conflicts += batch_conflicts
        total_new += batch_new
        print(f"  -> Batch summary: NEW={batch_new}, EXISTS={batch_exists}, CONFLICTS={batch_conflicts}, TOTAL={batch_new + batch_exists + batch_conflicts}")

    print("\n=== SUMMARY ===")
    print(f"Batches ready: {total_batches}")
    print(f"Total planned vaults: {total_vaults}")
    print(f"Total NEW: {total_new}")
    print(f"Total EXISTS (exact name): {total_exists}")
    print(f"Total CONFLICTS (canonical): {total_conflicts}")