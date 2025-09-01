import uuid

from app.config.parser import args
from app.services.create_vaults_with_retries import try_create_vault
from app.services.load_project_inputs import load_all_inputs, summarize_scan
from app.services.who_am_i import try_get_uuid


def main():
    print("1-PASSWORD-MANAGER: Running application-----------------------------------")
    print("ONSTART: Get-Identity")
    my_uuid: str = try_get_uuid()
    created_vaults = []

    if args.from_inputs:
        print("BRANCH: Batch-From-Inputs")
        # For now, we just summarize. Next step: iterate and create vaults w/ receipts
        scan = load_all_inputs()
        print("\tSCAN: Printing-Inputs-Summary")
        print(summarize_scan(scan))
        print("\tSCAN: Scan-Complete")
        return

    elif args.create_one:
        print("BRANCH: Create-Single-Vault")
        if args.name:
            print("STAGE: Create-From-User-Provided-Name")
            try_create_vault(args.named_vault)
            created_vaults.append(args.named_vault)  # TODO - add error handling
        elif args.random_vault:
            print("STAGE: Create-Vault-With-Random-Suffix")
            random_name = "PY-VAULT-" + uuid.uuid4().hex[:8]
            try_create_vault(random_name)
            created_vaults.append(random_name)  # TODO - add error handling
        else:
            print("ERROR: --create-one requires either --name or --random")

    # TODO: persist created_vaults + add rollback record(s)
    else:
        print("WARN: no flags provided, exiting")


main()
