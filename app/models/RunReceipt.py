from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.PacificDatetime import PacificDatetime


class VaultSuccess(BaseModel):
    batch_name: str
    project: str
    vault_name: str
    vault_id: Optional[str] = None


class VaultFailure(BaseModel):
    batch_name: str
    project: str
    vault_name: str
    error: str


class RunReceipt(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    actor_uuid: str
    started_at: PacificDatetime
    finished_at: PacificDatetime

    input_files: List[str]
    warnings: List[str] = Field(default_factory=list)  # file-level warnings aggregated
    errors: List[str] = Field(default_factory=list)  # file-level warnings aggregated

    successes: List[VaultSuccess] = Field(default_factory=list)
    failures: List[VaultFailure] = Field(default_factory=list)
