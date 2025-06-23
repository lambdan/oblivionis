import datetime
from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn

from oblivionis import bot
from oblivionis import steamgriddb
from oblivionis.models import GameWithStats, PaginatedResponse, PlatformWithStats, UserWithStats
from oblivionis.storage.storage_v2 import User, Game, Platform, Activity

app = FastAPI()

def validateLimitOffset(limit: int|str, offset: int|str, maxLimit=50):
    if not (1 <= int(limit) <= maxLimit):
        raise HTTPException(status_code=400, detail="Limit must be between 1 and " + str(maxLimit))
    if int(offset) < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")
    return int(limit), int(offset)

def fixDatetime(data):
    """
    Recursively converts datetime objects in a dictionary to milliseconds since epoch
    """
    if isinstance(data, datetime.datetime):
        if data.tzinfo is None:
            data = data.replace(tzinfo=datetime.timezone.utc)
        return int(data.timestamp() * 1000)
    
    if not isinstance(data, (dict, list)):
        return data
    
    if isinstance(data, dict):
        return {k: fixDatetime(v) for k, v in data.items()}
    
    if isinstance(data, list):
        return [fixDatetime(item) for item in data]




@app.get("/api/users/{userId}")
def get_user(userId: int):
    user = User.get_or_none(User.id == userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data: UserWithStats = {
        "user": model_to_dict(user),  # type: ignore
        "last_played": get_last_activity(userid=user.id)["timestamp"], # type: ignore
        "total_activities":  get_activity_count(userId=user.id),
        "total_playtime":  get_total_playtime(userId=user.id),
    }
    return fixDatetime(data)

@app.get("/api/users")
def get_users(offset=0, limit=25):
    limit, offset = validateLimitOffset(limit, offset)
    response: PaginatedResponse = {
        "data": [],
        "_total": User.select().count(),
        "_offset": offset,
        "_limit": limit,
    }
    for user in User.select().limit(limit).offset(offset):
        response["data"].append(get_user(user.id))
    return fixDatetime(response)

@app.get("/api/users/{userId}/games")
def get_user_games(userId: int, offset = 0, limit = 25):
    limit, offset = validateLimitOffset(limit, offset)
    user = User.get_or_none(User.id == userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).where(Activity.user == userId).distinct()
    games = games[int(offset):int(offset) + int(limit)]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id, userId=user.id)
        response.append(game_data)

    paginatedResponse: PaginatedResponse = {
        "data": response,
        "_total": get_game_count(userId=user.id),
        "_offset": offset,
        "_limit": limit,
    }

    return fixDatetime(paginatedResponse)


@app.get("/api/users/{user_id}/stats")
def get_user_stats(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    oldest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.asc()).first()
    newest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).first()
    total_playtime = get_total_playtime(userId=user.id)
    total_activities = get_activity_count(userId=user.id)
    total_games = get_game_count(userId=user.id)
    total_platforms = get_platform_count(userId=user.id)

    return fixDatetime({
        "total": {
            "seconds": total_playtime,
            "activities": total_activities,
            "games": total_games,
            "platforms": total_platforms
        },
        "oldest_activity": model_to_dict(oldest_activity) if oldest_activity else None,
        "newest_activity": model_to_dict(newest_activity) if newest_activity else None,
        "active_days": Activity.select(fn.COUNT(fn.DISTINCT(fn.DATE(Activity.timestamp)))).where(Activity.user == user).scalar(),
        "average": {
            "seconds_per_game": total_playtime / total_games if total_games > 0 else 0,
            "sessions_per_game": total_activities / total_games if (total_activities > 0 and total_games > 0) else 0,
            "session_length": total_playtime / total_activities if (total_activities > 0 and total_playtime > 0) else 0,
        }
    })

#################
# Activities
#################

@app.get("/api/activities")
def list_activities(offset = 0, limit = 25, order = "desc", user: int | None = None, game: int | None = None, platform: int | None = None):
    limit, offset = validateLimitOffset(limit, offset)
    activities = [model_to_dict(activity) for activity in 
        Activity.select().offset(offset).limit(limit).order_by(Activity.timestamp.desc() if order == "desc" else Activity.timestamp.asc())
        .where(
            (Activity.user == user) if user is not None else True,
            (Activity.game == game) if game is not None else True,
            (Activity.platform == platform) if platform is not None else True
        )]
    response = {
        "data": activities,
        "_total": Activity.select().where(
            (Activity.user == user) if user is not None else True,
            (Activity.game == game) if game is not None else True,
            (Activity.platform == platform) if platform is not None else True
        ).count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return fixDatetime(response)


@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int):
    activity = Activity.get_or_none(Activity.id == activity_id) # type: ignore
    return fixDatetime(model_to_dict(activity)) if activity else {"error": "Not found"}

@app.get("/api/last_activity")
def get_last_activity(userid: int | None = None, gameid: int | None = None, platformid: int | None = None):
    """
    Returns the last activity for a user, game or platform.
    If no parameters are given, returns the last activity overall.
    """
    query = Activity.select().order_by(Activity.timestamp.desc())
    
    if userid:
        query = query.where(Activity.user == userid)
    if gameid:
        query = query.where(Activity.game == gameid)
    if platformid:
        query = query.where(Activity.platform == platformid)

    last_activity = query.first()
    
    if not last_activity:
        raise HTTPException(status_code=404, detail="No activity found")

    return fixDatetime(model_to_dict(last_activity))

##############
# Games
#############

@app.get("/api/games")
def get_games(limit = 25, offset = 0):
    limit, offset = validateLimitOffset(limit, offset)

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).distinct()
    games = games[int(offset):int(offset) + int(limit)]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id)
        response.append(game_data)

    paginatedResponse: PaginatedResponse = {
        "data": response,
        "_total": get_game_count(),
        "_offset": offset,
        "_limit": limit,
    }

    return fixDatetime(paginatedResponse)

@app.get("/api/games/{gameId}")
def get_game(gameId: int, userId: int | None = None):
    game = Game.get_or_none(Game.id == gameId) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    entry: GameWithStats ={
        "game": model_to_dict(game),  # type: ignore
        "total_playtime": get_total_playtime(userId=userId, gameId=game.id),
        "last_played": get_last_activity(userid=userId, gameid=game.id)["timestamp"], # type: ignore
        "total_sessions": get_activity_count(userId=userId, gameId=game.id),
    }

    return fixDatetime(entry)



##############
# Platforms
##############
@app.get("/api/platforms/{platform_id}")
def get_platform(platform_id: int):
    platform = Platform.get_or_none(Platform.id == platform_id) # type: ignore
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    total_playtime_all_platforms = get_total_playtime()
    playtime_this_platform = Activity.select(fn.SUM(Activity.seconds)).where(Activity.platform == platform).scalar() or 0

    data: PlatformWithStats = {
        "platform": model_to_dict(platform), # type: ignore
        "last_played": Activity.select(fn.MAX(Activity.timestamp)).where(Activity.platform == platform).scalar() or None,
        "total_sessions": Activity.select().where(Activity.platform == platform).count(),
        "total_playtime": playtime_this_platform,
        "percent": playtime_this_platform / total_playtime_all_platforms 
    } 
    return fixDatetime(data)

@app.get("/api/platforms")
def list_platforms(offset=0, limit=25):
    limit, offset = validateLimitOffset(limit, offset)
    platforms = Platform.select().limit(limit).offset(offset)

    response: PaginatedResponse = {
        "data": [], # type: ignore
        "_total": Platform.select().count() ,
        "_offset": offset,
        "_limit": limit,
    }

    for platform in platforms:
        response["data"].append(get_platform(platform.id))
    return fixDatetime(response)

#################
# Totals
#################

@app.get("/api/stats")
def get_stats():
    return {
        "total_playtime": get_total_playtime(),
        "activities": get_activity_count(),
        "users": get_user_count(),
        "games": get_game_count(),
        "platforms": get_platform_count(),
    }

@app.get("/api/stats/total_playtime")
def get_total_playtime(userId: int | None = None, gameId: int | None = None, platformId: int | None = None) -> int:
    query = Activity.select(fn.SUM(Activity.seconds))
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    if conditions:
        query = query.where(*conditions)
    return query.scalar() or 0

@app.get("/api/stats/total_activities")
def get_activity_count(userId: int | None = None, gameId: int | None = None) -> int:
    if userId and gameId:
        return Activity.select().where(
            (Activity.user == userId) & (Activity.game == gameId)
        ).count()
    if userId:
        return Activity.select().where(
            Activity.user == userId
        ).count()
    if gameId:
        return Activity.select().where(
            Activity.game == gameId
        ).count()
    return Activity.select().count()

@app.get("/api/stats/total_users")
def get_user_count() -> int:
    return User.select().count()

@app.get("/api/stats/total_games")
def get_game_count(userId: int | None = None) -> int:
    # iterating over Activity to only get games with activity
    if userId:
        return Activity.select(Activity.game).where(Activity.user == userId).distinct().count()
    return Activity.select(Activity.game).distinct().count()

@app.get("/api/stats/total_platforms")
def get_platform_count(userId: int | None = None, gameId: int | None = None) -> int:
    if userId and gameId:
        return Activity.select(Activity.platform).where(
            (Activity.user == userId) & (Activity.game == gameId)
        ).distinct().count()
    if userId:
        return Activity.select(Activity.platform).where(
            Activity.user == userId
        ).distinct().count()
    if gameId:
        return Activity.select(Activity.platform).where(
            Activity.game == gameId
        ).distinct().count()
    return Activity.select(Activity.platform).distinct().count()

###############
# SteamGridDB
###############

@app.get("/api/sgdb/search")
def search_sgdb(query: str):
    return steamgriddb.search(query)

@app.get("/api/sgdb/grids/{game_id}")
def grid_sgdb(game_id: int):
    grids = steamgriddb.get_grids(game_id)
    return grids 

@app.get("/api/sgdb/grids/{game_id}/best")
def best_grid_sgdb(game_id: int):
    best = steamgriddb.get_best_grid(game_id)
    if not best:
        raise HTTPException(status_code=404, detail="Not found")
    return best

###############
# Discord
###############

@app.get("/api/discord/{discord_user_id}/avatar")
def get_discord_avatar(discord_user_id: int):
    return {"url": bot.avatar_from_discord_user_id(discord_user_id)}