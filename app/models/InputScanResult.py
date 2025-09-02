from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.InputFileParseResult import InputFileParseResult


class InputScanResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    prefix_files: List[InputFileParseResult] = Field(default_factory=list)
    suffix_files: List[InputFileParseResult] = Field(default_factory=list)
    fatal_errors: List[str] = Field(default_factory=list)

    # Transitional compatibility: old code may reference `scan.files`
    @property
    def files(self) -> List[InputFileParseResult]:
        return [*self.prefix_files, *self.suffix_files]
