import datetime
from typing import TypedDict


class ActivityAssets(TypedDict):
    small_image_url: str | None
    large_image_url: str | None

class ManualSession(TypedDict):
    gameName: str
    platform: str | None
    startTime: datetime.datetime