# 1-Password-Manager
Demo project to showcase account management capabilities of the 1Password CLI tools

### Usage

#### Example of creating a random vault...

```
python -m app.main --random-vault
```

#### IDE Notes
- Pylance plugin: might show an error while importing `pydantic`
  - Pylance will use 3.9 per `.python-version`, but VS Code doesn't know to use your virtual environment
  - fix: hover over the error and choose Select Interpretter. Chose `(venv) 3.9` instead of the default `3.9`

### Requirements: 1Password Service Accounts

This project requires a 1Password Service Account. You cannot be signed in as any type of natural user (e.g. Member, Administrator, Owner). This program relies on the existence of a Service Account with the appropriate permissions (create vaults, grant user access)

<details><summary>Click to see more info on Service Accounts</summary>

---

#### Value Prop:

Source: https://developer.1password.com/docs/service-accounts/get-started

> With 1Password Service Accounts, you can build tools to automate secrets management in your applications and infrastructure without deploying additional services.

Service accounts can:

- Create, edit, delete, and share items.
- Create vaults.
- Delete vaults.
  - a service account can only delete a vault it created

#### Usage
Requirements: User (CLI or 1Password site) needs to be an Owner or Administrator
- Owners/Administrators can create a new Group with permissions to create Service Account (niche)

```
op service-account create <serviceAccountName> --expires-in <duration> --vault <vault-name:<permission>,<permission>
```
- Available permissions: read_items, write_items (requires read_items), share_items (requires read_items)
- Include the `--can-create-vaults` flag to allow the service account to create new vaults.

</br>

**WARNING**: 1Password CLI only returns the service account token once. Save the token in 1Password immediately to avoid losing it. Treat this token like a password, and don't store it in plaintext.

---

</details>




