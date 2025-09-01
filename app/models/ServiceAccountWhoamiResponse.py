from typing import Literal

from pydantic import BaseModel, HttpUrl


class ServiceAccountWhoamiResponse(BaseModel):
    url: HttpUrl
    user_uuid: str
    account_uuid: str
    user_type: Literal["SERVICE_ACCOUNT"]
