# app/services/list_vaults.py
from __future__ import annotations

from typing import Dict, Set, Tuple

from app.config.settings import settings
from app.models.SubprocessResponse import OpStatus
from app.models.VaultListItem import VaultListItem
from app.services.exc import CommandFailureError, RateLimitedError
from app.services.run_command import op_list_vaults


def normalize_vault_name(name: str) -> str:
    """
    Normalize for duplicate checks.
    - Trim whitespace always.
    - Case-insensitive unless settings.caseSensitiveVaultNames is True.
    """
    case_sensitive = getattr(settings, "caseSensitiveVaultNames", False)
    s = name.strip()
    return s if case_sensitive else s.casefold()


def get_existing_vault_index() -> Tuple[Dict[str, VaultListItem], Set[str]]:
    """
    Returns:
      - by_name_norm: dict of normalized_name -> VaultListItem
      - names_norm: set of normalized names (for fast membership checks)
    Raises on failure (rate limit / command errors).
    """
    sr = op_list_vaults()
    if sr.status == OpStatus.SUCCESS:
        items = [VaultListItem.model_validate(x) for x in sr.formatted_output]
        by_name = {normalize_vault_name(v.name): v for v in items}
        return by_name, set(by_name.keys())
    if sr.status == OpStatus.RATE_LIMITED:
        raise RateLimitedError("`op vault list` rate-limited.", retry_after_minutes=10)
    raise CommandFailureError(
        command="op vault list", return_code=sr.return_code, stderr=sr.error
    )
