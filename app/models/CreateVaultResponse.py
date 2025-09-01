from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateVaultResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    name: str
    content_version: int
    created_at: datetime
    updated_at: datetime
    items: int
    attribute_version: int
    type: str
