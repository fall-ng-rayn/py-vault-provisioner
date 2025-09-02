from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer


def to_pacific(dt: datetime) -> datetime:
    """
    Convert an aware or naive datetime to America/Los_Angeles.
    - Naive -> assumed UTC.
    - Aware -> converted to America/Los_Angeles.
    """
    pac = ZoneInfo("America/Los_Angeles")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(pac)
    # tz = ZoneInfo("America/Los_Angeles")
    # return datetime.now(tz=tz)


def to_iso_pacific(dt: datetime) -> str:
    return to_pacific(dt).isoformat()


PacificDatetime = Annotated[datetime, PlainSerializer(to_iso_pacific, return_type=str)]
