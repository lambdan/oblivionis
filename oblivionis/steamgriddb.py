import datetime
import os, logging
from typing import TypedDict
from steamgrid import SteamGridDB
from steamgrid import StyleType, PlatformType, MimeType, ImageType


logger = logging.getLogger("SteamGridDB")
ONE_DAY = 24 * 60 * 60 # seconds
sgdb = SteamGridDB(os.environ["SGDB_TOKEN"])
cache = {}

def search(query: str):
    cacheKey = "search_" + query
    if cacheKey in cache:
        time: datetime.datetime = cache[cacheKey]["time"]
        delta = datetime.datetime.now(datetime.UTC) - time
        if delta.total_seconds() < ONE_DAY:
            logger.debug("Returning cached search result for query '%s'", query)
            return cache[cacheKey]["data"]
    
    cacheEntry = {
        "time": datetime.datetime.now(datetime.UTC),
        "data": sgdb.search_game(query)
    }
    cache[cacheKey] = cacheEntry
    return cache[cacheKey]["data"]

def get_grids(game_id: int):
    cacheKey  = "grids_" + str(game_id)
    if cacheKey in cache:
        time: datetime.datetime = cache[cacheKey]["time"]
        delta = datetime.datetime.now(datetime.UTC) - time
        if delta.total_seconds() < ONE_DAY:
            logger.debug("Returning cached grids for game ID %d", game_id)
            return cache[cacheKey]["data"]
        
    logger.debug("Fetching grids for game ID %d from SteamGridDB", game_id)
    cache[cacheKey] = {
        "time": datetime.datetime.now(datetime.UTC),
        "data": sgdb.get_grids_by_gameid(game_ids=[game_id], styles=[StyleType.Alternate], mimes=[MimeType.PNG, MimeType.JPEG, MimeType.WEBP], is_nsfw=False)
    }
    return cache[cacheKey]["data"]

def get_best_grid(game_id: int):
    grids = get_grids(game_id)
    if not grids:
        return None

    bestScore = 0
    bestGrid = None
    for grid in grids:
        thisScore = 0

        if grid.style == StyleType.Alternate:
            thisScore += 10

        if grid.language == "en":
            thisScore += 1

        if grid.width == 600 and grid.height == 900:
            thisScore += 1

        thisScore += grid.upvotes or 0
        thisScore -= grid.downvotes or 0

        if thisScore > bestScore:
            bestScore = thisScore
            bestGrid = grid

    return bestGrid
    

