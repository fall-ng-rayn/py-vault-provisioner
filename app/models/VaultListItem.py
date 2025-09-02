# app/models/VaultListItem.py
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class VaultListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")  # ignore fields we don't use
    id: str
    name: str
    content_version: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: Optional[int] = None
