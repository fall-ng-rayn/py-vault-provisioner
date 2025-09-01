from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.InputFileResult import InputFileResult


class InputScanResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    files: List[InputFileResult] = Field(default_factory=list)
    fatal_errors: List[str] = Field(default_factory=list)
