import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OpStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RATE_LIMITED = "rate-limited"
    UNKNOWN = "unknown"


JSON_EMIT_CMDS = ["create", "list", "get", "whoami"]


class SubprocessResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    command: str
    status: OpStatus = Field(default=OpStatus.UNKNOWN)
    formatted_output: dict = Field(default_factory=dict)
    output: str
    error: str
    return_code: int

    @model_validator(mode="after")
    def _populate_status_and_output(self):
        if "rate-limited" in self.error:
            self.status = OpStatus.RATE_LIMITED
        elif self.return_code != 0:
            self.status = OpStatus.FAILURE
        elif any([c in self.command for c in JSON_EMIT_CMDS]):
            self.status = OpStatus.SUCCESS
            self.formatted_output = json.loads(self.output)
        else:
            self.status = OpStatus.SUCCESS
        return self
