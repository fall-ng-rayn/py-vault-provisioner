# app/services/list_vaults.py
from __future__ import annotations
import re
from typing import Dict, Tuple, Set, List

from app.config.settings import settings
from app.models.SubprocessResponse import OpStatus
from app.models.VaultListItem import VaultListItem
from app.services.run_command import op_list_vaults
from app.services.exc import RateLimitedError, CommandFailureError

_WS_DASH_RE = re.compile(r"[ \-]+")

def normalize_vault_name(name: str) -> str:
    """
    Exact-match normalization.
    - Always .strip()
    - Case-insensitive unless settings.caseSensitiveVaultNames is True
    """
    case_sensitive = getattr(settings, "caseSensitiveVaultNames", False)
    s = name.strip()
    return s if case_sensitive else s.casefold()

def canonical_vault_key(name: str) -> str:
    """
    Fuzzy-match canonicalization:
    - Trim
    - Lowercase (casefold)
    - Remove spaces and dashes entirely
    Example: "P: 311 - Data -lead" -> "p:311datalead"
    """
    s = name.strip().casefold()
    return _WS_DASH_RE.sub("", s)

def get_existing_vault_indexes() -> Tuple[
    Dict[str, VaultListItem], Set[str],           # exact: by_name_norm, names_norm
    Dict[str, List[VaultListItem]], Set[str]      # canonical: by_canon, canon_keys
]:
    """
    Build both exact and canonical indexes from `op vault list`.
    """
    sr = op_list_vaults()
    if sr.status == OpStatus.SUCCESS:
        items = [VaultListItem.model_validate(x) for x in sr.formatted_output]

        by_name_norm: Dict[str, VaultListItem] = {}
        by_canon: Dict[str, List[VaultListItem]] = {}

        for v in items:
            # exact
            by_name_norm[normalize_vault_name(v.name)] = v
            # canonical (may map to multiple)
            ck = canonical_vault_key(v.name)
            by_canon.setdefault(ck, []).append(v)

        return by_name_norm, set(by_name_norm.keys()), by_canon, set(by_canon.keys())

    if sr.status == OpStatus.RATE_LIMITED:
        raise RateLimitedError("`op vault list` rate-limited.", retry_after_minutes=10)
    raise CommandFailureError(return_code=sr.return_code, stderr=sr.error)
