import uuid

from app.config.parser import args
from app.services.batch_from_inputs import run_from_inputs
from app.services.create_vaults_with_retries import try_create_vault
from app.services.delete_last_run import delete_last_run
from app.services.load_project_inputs import load_all_inputs, summarize_scan
from app.services.preview_from_inputs import preview_from_inputs
from app.services.who_am_i import try_get_uuid


def main():
    print("1-PASSWORD-MANAGER: Running application-----------------------------------")
    print("ONSTART: Get-Identity")
    actor_uuid: str = try_get_uuid()

    if args.preview_from_inputs:
        print("BRANCH: Preview-From-Inputs")
        print("STAGE: Previewing-Inputs")
        preview_from_inputs()
        return

    if args.from_inputs:
        print("BRANCH: Batch-From-Inputs")
        scan = load_all_inputs()
        print("STAGE: Printing-Inputs-Summary")
        print("\tSCAN------------------------")
        print(summarize_scan(scan))
        print("\tSCAN: Scan-Complete---------")

        print("STAGE: Batch-And-Write-Receipts")
        run_from_inputs(actor_uuid)
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
        elif args.random_vault:
            print("STAGE: Create-Vault-With-Random-Suffix")
            random_name = "PY-VAULT-" + uuid.uuid4().hex[:8]
            try_create_vault(random_name)
        else:
            print("ERROR: --create-one requires either --name or --random")

    else:
        print("WARN: no flags provided, exiting")


main()
