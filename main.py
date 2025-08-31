from argparse import ArgumentParser
import uuid
from lib.create_vaults import create_vault
from lib.whoami import get_my_uuid


parser = ArgumentParser(
    prog="1-Password-Manager",
    description="Various helper tools designed to help automate 1Password account management",
)

parser.add_argument(
    "--named-vault",
    action="store",
    dest="named_vault",
    help="Create a single vault, given a vault name"
)

parser.add_argument(
    "--random-vault",
    action="store_true",
    dest="random_vault",
    help="create a singl vault with a random name"
)

parser.add_argument(
    "--remove-me",
    action="store_true",
    dest="removeMe",
    help="Remove yourself from the vaults created by this script. To avoid rate limiting, this aggressively throttles the script and each vault will take 11 seconds to process.",
)

args = parser.parse_args()


def main():
    print("1-PASSWORD-MANAGER: Running application-----------------------------------")
    my_uuid: str = get_my_uuid()

    if args.named_vault:
        print('STAGE: Create-Single-Vault')
        create_vault(args.named_vault)
    elif args.random_vault:
        print('STAGE: Create-Single-Random-Vault')
        create_vault('PY-VAULT-' + uuid.uuid4().hex[:8])

main()
