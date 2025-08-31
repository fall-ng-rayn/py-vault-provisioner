import uuid

from app.config.parser import args
from app.services.create_vaults_with_retries import try_create_vault
from app.services.who_am_i import get_my_uuid


def main():
    print("1-PASSWORD-MANAGER: Running application-----------------------------------")
    my_uuid: str = get_my_uuid()
    created_vaults = []

    # TODO - need some way of remembering what vaults we successfully made
    # so we can "remove ourselves" after

    if args.named_vault:
        print("STAGE: Create-Single-Vault")
        try_create_vault(args.named_vault)
        created_vaults.append(args.named_vault)  # TODO - no error checking
    elif args.random_vault:
        print("STAGE: Create-Single-Random-Vault")
        random_name = "PY-VAULT-" + uuid.uuid4().hex[:8]
        try_create_vault(random_name)
        created_vaults.append(random_name)  # TODO - no error checking

    if args.removeMe:
        print("STAGE: Remove-User-Permissions")
        for vault in created_vaults:
            # remove-permissions()
            print(vault)

    # TODO -- now we need to write code that remembers all of the records that we've created
    # so far (so we can split up vaults we actually-created vs ones that we were supposed
    # to create but failed to complete... so we can pick up where we left off in case of a
    # problem with the pipeline).
    # I think maybe we could just keep an in-memory list, and then write that to file
    # if it goes wrong? Or maybe better to just write to file as we go so we don't lose
    # progress...

    # TODO -- we also gotta write the code to remove ourselves off the vaults that we've
    # just created... otherwise we gna have so many vaults associated with our account


main()
