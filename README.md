# 1-Password-Manager
Demo project to showcase account management capabilities of the 1Password CLI tools

### Project Info

#### Example of creating a random vault...

```
python -m app.main --random-vault
```

#### IDE Notes
- Pylance plugin: might show an error while importing `pydantic`
  - Pylance will use 3.9 per `.python-version`, but VS Code doesn't know to use your virtual environment
  - fix: hover over the error and choose Select Interpretter. Chose `(venv) 3.9` instead of the default `3.9`

### 1Password: Service Accounts
Value Prop:
> With 1Password Service Accounts, you can build tools to automate secrets management in your applications and infrastructure without deploying additional services.

Service accounts can:

- Create, edit, delete, and share items.
- Create vaults.
- Delete vaults.
  - a service account can only delete a vault it created

Source: https://developer.1password.com/docs/service-accounts/get-started


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
