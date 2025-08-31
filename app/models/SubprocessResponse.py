import json
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class OpStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RATE_LIMITED = "rate-limited"
    UNKNOWN = "unknown"


class SubprocessResponse(BaseModel):
    status: OpStatus = Field(default=OpStatus.UNKNOWN)
    formatted_output: dict = Field(default={})
    output: str
    error: str
    return_code: int

    @model_validator(mode="after")
    def _populate_status_and_output(self):
        if "rate-limited" in self.error:
            self.status = OpStatus.RATE_LIMITED
        elif self.return_code != 0:
            self.status = OpStatus.FAILURE
        else:
            self.status = OpStatus.SUCCESS
            self.formatted_output = json.loads(self.output)
        return self
