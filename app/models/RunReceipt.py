from datetime import datetime
from typing import Annotated, List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


def to_pacific(dt: datetime) -> datetime:
    tz = ZoneInfo("America/Los_Angeles")
    return datetime.now(tz=tz)


def to_iso_pacific(dt: datetime) -> str:
    return to_pacific(dt).isoformat()


PacificDatetime = Annotated[datetime, PlainSerializer(to_iso_pacific, return_type=str)]


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
