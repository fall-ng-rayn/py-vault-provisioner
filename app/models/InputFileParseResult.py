from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class InputFileParseResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["prefixes", "suffixes"]
    batch_name: str  # e.g. "active-projects" from "active-projects-vault-prefixes.txt"
    path: Path
    projects: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
