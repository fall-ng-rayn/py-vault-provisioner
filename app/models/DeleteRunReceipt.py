# app/models/DeleteRunReceipt.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.PacificDatetime import PacificDatetime


class VaultDeleteSuccess(BaseModel):
    vault_id: Optional[str] = None
    vault_name: str
    batch_name: Optional[str] = None
    project: Optional[str] = None


class VaultDeleteFailure(BaseModel):
    vault_id: Optional[str] = None
    vault_name: str
    error: str
    batch_name: Optional[str] = None
    project: Optional[str] = None


class DeleteRunReceipt(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id_deleted: str
    source_rollback_file: str
    actor_uuid: str
    started_at: PacificDatetime
    finished_at: PacificDatetime

    dry_run: bool = False
    planned: List[VaultDeleteSuccess] = Field(default_factory=list)
    successes: List[VaultDeleteSuccess] = Field(default_factory=list)
    failures: List[VaultDeleteFailure] = Field(default_factory=list)
