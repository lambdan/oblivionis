import datetime
from typing import TypedDict

from oblivionis.storage.storage_v2 import Game, Platform


class ActivityAssets(TypedDict):
    small_image_url: str | None
    large_image_url: str | None

class ManualSession(TypedDict):
    game: Game
    platform: Platform
    startTime: datetime.datetime