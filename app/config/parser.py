from argparse import ArgumentParser

parser = ArgumentParser(
    prog="vault-manager",
    description="Various helper tools designed to help automate 1Password account management",
)

mode = parser.add_mutually_exclusive_group()

# branch: --create-one
mode.add_argument(
    "--create-one",
    action="store_true",
    help="Create a single vault (use with --name or --random)",
)

parser.add_argument(
    "--name",
    action="store",
    dest="name",
    help="creates a single vault, using the provided vault name",
)

parser.add_argument(
    "--random",
    action="store_true",
    dest="random",
    help="creates a single vault with a random name",
)

# branch: --from-inputs
mode.add_argument(
    "--from-inputs",
    action="store_true",
    help="Batch mode: read ./input/*-vault-prefixes.txt and prepare projects for processing",
)

# branch: --delete-last-run
mode.add_argument(
    "--delete-last-run",
    action="store_true",
    help="Delete all vaults listed in the most recent run's rollback.jsonl.",
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not perform deletions; only print what would be deleted and ouput the deletion receipt",
)
parser.add_argument(
    "--run-id",
    dest="run_id",
    help="Target a specific run id (subfolder of output/runs) for --delete-last-run",
)

args = parser.parse_args()
