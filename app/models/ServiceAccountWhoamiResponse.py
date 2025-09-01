from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl


class ServiceAccountWhoamiResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    url: HttpUrl
    user_uuid: str
    account_uuid: str
    user_type: Literal["SERVICE_ACCOUNT"]
