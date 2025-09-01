from argparse import ArgumentParser

parser = ArgumentParser(
    prog="vault-manager",
    description="Various helper tools designed to help automate 1Password account management",
)

parser.add_argument(
    "--create-one",
    action="store_true",
    dest="create_one",
    help="signals to the program that we will make one vault",
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
    dest="random_vault",
    help="creates a single vault with a random name",
)


args = parser.parse_args()
