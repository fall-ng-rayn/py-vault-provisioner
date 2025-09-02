from argparse import ArgumentParser, RawDescriptionHelpFormatter

parser = ArgumentParser(
    prog="vault-manager",
    description="Utilities to provision and clean up 1Password vaults.",
    formatter_class=RawDescriptionHelpFormatter,
    epilog=(
        "Examples:\n"
        "  Create one named vault:\n"
        "    vault-manager --create-one --name 'Project X - Engineer'\n\n"
        "  Preview vaults from inputs (no changes):\n"
        "    vault-manager --preview-from-inputs\n\n"
        "  Batch-create from inputs:\n"
        "    vault-manager --from-inputs\n\n"
        "  Delete latest run (dry run):\n"
        "    vault-manager --delete-last-run --dry-run\n\n"
        "  Delete a specific run:\n"
        "    vault-manager --delete-last-run --run-id 2025-09-01_16-47-00-0700_ab12cd\n"
    ),
)

# Mutually-exclusive modes
mode = parser.add_mutually_exclusive_group()
mode.add_argument(
    "--create-one",
    action="store_true",
    help="Create a single vault (use with one of --name/--random).",
)
mode.add_argument(
    "--from-inputs",
    action="store_true",
    help="Create vaults from ./input/*-vault-{prefixes,suffixes}.txt.",
)
mode.add_argument(
    "--preview-from-inputs",
    action="store_true",
    help="Preview vault names from input files (no changes).",
)
mode.add_argument(
    "--delete-last-run",
    action="store_true",
    help="Delete vaults listed in the latest run's rollback.jsonl.",
)

# Create options (mutually exclusive)
create_opts = parser.add_argument_group("Create options")
create_choice = create_opts.add_mutually_exclusive_group()
create_choice.add_argument(
    "--name",
    dest="name",
    help="Vault name to create (with --create-one).",
)
create_choice.add_argument(
    "--random",
    action="store_true",
    dest="random",
    help="Create with a random name (with --create-one).",
)

# Delete options
delete_opts = parser.add_argument_group("Delete options")
delete_opts.add_argument(
    "--dry-run",
    action="store_true",
    help="Print actions only; write a receipt but do not delete.",
)
delete_opts.add_argument(
    "--run-id",
    dest="run_id",
    help="Target a specific run folder under output/runs (with --delete-last-run).",
)

args = parser.parse_args()
