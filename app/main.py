import uuid

from app.config.parser import args
from app.services.batch_from_inputs import run_from_inputs
from app.services.create_vaults_with_retries import try_create_vault
from app.services.delete_last_run import delete_last_run
from app.services.load_project_inputs import load_all_inputs, summarize_scan
from app.services.who_am_i import try_get_uuid


def main():
    print("1-PASSWORD-MANAGER: Running application-----------------------------------")
    print("ONSTART: Get-Identity")
    actor_uuid: str = try_get_uuid()
    created_vaults = []

    if args.from_inputs:
        print("BRANCH: Batch-From-Inputs")
        # For now, we just summarize. Next step: iterate and create vaults w/ receipts
        scan = load_all_inputs()
        print("STAGE: Printing-Inputs-Summary")
        print("\tSCAN------------------------")
        print(summarize_scan(scan))
        print("\tSCAN: Scan-Complete---------")

        print("STAGE: Batch-And-Write-Receipts")
        run_dir = run_from_inputs(actor_uuid)
        return

    if args.delete_last_run:
        print("BRANCH: Delete-Last-Run")
        receipt_path = delete_last_run(run_id=args.run_id, dry_run=args.dry_run)
        print(f"Artifacts written to: {receipt_path.parent}")
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

    else:
        print("WARN: no flags provided, exiting")


main()
