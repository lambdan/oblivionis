import datetime
from typing import Any, TypedDict

from oblivionis.storage.storage_v2 import Game, Platform, User


class ActivityAssets(TypedDict):
    small_image_url: str | None
    large_image_url: str | None

class ManualSession(TypedDict):
    game: Game
    platform: Platform
    startTime: datetime.datetime

class PaginatedResponse(TypedDict):
    data: Any = None # type: ignore
    _total: int
    _offset: int
    _limit: int

class PlatformWithStats(TypedDict):
    platform: Platform
    last_played: datetime.datetime | None
    total_sessions: int
    total_playtime: int
    percent: float

class UserWithStats(TypedDict):
    user: User
    last_played: datetime.datetime | None
    total_sessions: int
    total_playtime: int

class GameWithStats(TypedDict):
    game: Game
    last_played: datetime.datetime | None
    total_sessions: int
    total_playtime: int