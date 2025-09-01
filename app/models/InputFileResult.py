from pathlib import Path
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class InputFileResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    batch_name: str  # e.g. "active-projects" from "active-projects-vault-prefixes.txt"
    path: Path
    projects: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
