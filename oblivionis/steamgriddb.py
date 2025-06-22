import os
from steamgrid import SteamGridDB
from steamgrid import StyleType, PlatformType, MimeType, ImageType


sgdb = SteamGridDB(os.environ["SGDB_TOKEN"])

def search(query: str):
    result = sgdb.search_game(query)
    return result

def get_grids(game_id: int):
    return sgdb.get_grids_by_gameid(game_ids=[game_id], styles=[StyleType.Alternate], mimes=[MimeType.PNG, MimeType.JPEG, MimeType.WEBP], is_nsfw=False)

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
    

