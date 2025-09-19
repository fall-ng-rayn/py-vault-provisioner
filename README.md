# Py Vault Provisioner

CLI utilities to **preview**, **provision**, and **clean up** 1Password vaults using a Service Account.  
Designed for batch jobs driven by simple text files, with receipts and rollback.

## Features

- **Preview mode**: shows exactly which vaults would be created (no changes)
- **Batch create**: cross-product of project inputs × role inputs
- **Duplicate guard**: skips names that already exist (`op vault list`)
- **Receipts**: per-run `receipt.json` and incremental `rollback.jsonl`
- **Safe cleanup**: `--delete-last-run` (with `--dry-run`), or target a specific run
- **Strong validation**: input file parsing with warnings/errors and batch skips

---

## Requirements

- **Python**: 3.9+ (project uses Pydantic v2)
- **1Password CLI**: `op` installed and on your PATH
- **1Password Service Account** with permissions to:
  - create vaults
  - grant user permissions
  - (optionally) delete vaults (a service account can only delete vaults it created)
- Service Account token available to the CLI (e.g., environment or `op signin` flow)

> Docs: https://developer.1password.com/docs/service-accounts/  
> **Security note:** the service account token is shown **once** on creation. Store it in 1Password immediately.

---

## Install

```bash
git clone <repo-url>
cd py-vault-provisioner

# (recommended) create a venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Optional config is in `app/config/settings.py` (see **Configuration**).

---

## Input Files

Place files in `./input/`:

- **Projects (prefixes)**: `*-vault-prefixes.txt`
- **Roles (suffixes)**: `*-vault-suffixes.txt`

The `*` becomes the **batch_name**. A batch is processed only if **both** files exist for the same `batch_name`. Missing one side → **skipped with a warning**.

Lines:
- One entry per line
- Blank lines and lines starting with `#` are ignored
- Validation: 1–63 chars, must start alphanumeric, allowed: letters, digits, spaces,'.' `-`, `_`, `:`
- Duplicates are ignored (warned)

**Example**
```
input/
├─ active-projects-vault-prefixes.txt
├─ active-projects-vault-suffixes.txt
└─ internal-tools-vault-prefixes.txt   # (no suffix file → skipped with warning)
```

`active-projects-vault-prefixes.txt`
```
# projects
Project-A
Project-B
```

`active-projects-vault-suffixes.txt`
```
# roles
Dev
Dev-Lead
PM
```

The tool will plan to create:
```
Project-A.Dev
Project-A.Dev-Lead
Project-A.PM
Project-A.PM-Lead
Project-B.Dev
Project-B.Dev-Lead
Project-B.PM
Project-B.PM-Lead
```

---

## Usage

All commands run via:

```bash
python -m app.main <flags>
```

### Preview (no changes)

```bash
python -m app.main --preview-from-inputs
```

- Reads `./input/*-vault-prefixes.txt` × `*-vault-suffixes.txt`
- Skips batches missing a side
- Prints the planned vault names and a summary

### Batch create

```bash
python -m app.main --from-inputs
```

- Validates inputs
- Skips batches missing a side
- **Checks existing vault names** via `op vault list`; skips duplicates
- Creates vaults
- Writes artifacts under `output/runs/<run_id>/`:
  - `batch_from_inputs-receipt.json` (successes, failures, warnings, input files)
  - `rollback.jsonl` (one JSON line per successful creation)

### Create one vault

```bash
python -m app.main --create-one --name "Project X - Engineer"
# or
python -m app.main --create-one --random
```

### Delete last run

```bash
# Dry run (recommended first)
python -m app.main --delete-last-run --dry-run

# Perform deletion
python -m app.main --delete-last-run
```

Target a specific run folder:

```bash
python -m app.main --delete-last-run --run-id 2025-09-01_16-47-00-0700_ab12cd
```

Writes `delete_last_run-receipt.json` into that run folder.

---

## Outputs (Artifacts)

Each batch run writes to `output/runs/<run_id>/`:

- `batch_from_inputs-receipt.json`  
  Summary: input files, aggregated warnings/errors, successes/failures with vault IDs (when available), timestamps.
- `rollback.jsonl`  
  One JSON object per **successful** vault creation; used by the delete command.
- `delete_last_run-receipt.json`  
  Written by delete command (supports `--dry-run` and `--run-id`).

Timestamps are emitted in **America/Los_Angeles** (configurable).

---

## Behavior Details

- **Cross-product per batch**: for each `batch_name`, create every `project` × `role`.
- **Skip if incomplete**: if the batch has only prefixes or only suffixes → skip with a warning.
- **Duplicate guard**: the tool calls `op vault list` once and **skips** any planned vault name that already exists (case-insensitive by default).
- **Retries & pacing**: rate limits and transient failures are retried (see `settings`).
- **Receipts & rollback**: successes are appended to `rollback.jsonl` as they happen, so partial progress is never lost.

---

## Configuration (selected)

Specified **only** in `.env`: (see: Service Accounts)

- `OP_SERVICE_ACCOUNT_TOKEN=[plaintext-token]`

Specified in `.env`, imported via `app/config/settings.py`. Common knobs:

- `usePacificTz` (bool): render timestamps in America/Los_Angeles (default: True)
- `shouldRetry` (bool): enable retries on rate limits/transients
- `maxRetries` (int): max attempts per create/delete
- `shouldBuffer` (bool): tiny sleeps between operations for pacing/log readability
- `caseSensitiveVaultNames` (bool): duplicate check case sensitivity (default: False)


Defined **only** in `app/config/settings.py`:

- `vaultNameJoiner` (str): joiner between project and role in the vault name (default: `"."`)

---

## Parser Help

```
Utilities to provision and clean up 1Password vaults.

Modes:
  --create-one              Create a single vault (use with one of --name/--random).
  --from-inputs             Create vaults from ./input/*-vault-{prefixes,suffixes}.txt.
  --preview-from-inputs     Preview vault names from input files (no changes).
  --delete-last-run         Delete vaults listed in the latest run's rollback.jsonl.

Create options:
  --name NAME               Vault name to create (with --create-one).
  --random                  Create with a random name (with --create-one).

Delete options:
  --dry-run                 Print actions only; write a receipt but do not delete.
  --run-id RUN_ID           Target a specific run folder under output/runs (with --delete-last-run).
```

---

## IDE Notes (VS Code / Pylance)

If Pylance flags `pydantic` imports:
- Ensure the interpreter is your project venv: **Command Palette → Python: Select Interpreter → .venv**
- Reopen the workspace if it keeps using a global Python

---

## Safety

- **Deletion**: consider archiving rather than hard delete if your policy requires it; adapt `op_delete_vault` flags accordingly.
- **Scope**: a service account can only delete vaults it created.
- **Credentials**: treat the service account token like a password; store in 1Password.

---

## Roadmap

- Granting permissions to users by Role
- CSV export of receipts
- JSON preview output (`--preview-from-inputs --as-json`)
- Per-run config overrides (e.g., custom joiner)  
- Batch “dry run” mode for create