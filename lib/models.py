
from datetime import datetime
from pydantic import BaseModel

class CreateVaultResponse(BaseModel):
    id: str
    name: str
    content_version: int
    created_at: datetime
    updated_at: datetime
    items: int
    attribute_version: int
    type: str