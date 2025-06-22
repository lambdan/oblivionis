from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn

from oblivionis import steamgriddb
from oblivionis.storage.storage_v2 import User, Game, Platform, Activity

app = FastAPI()

@app.get("/api/users")
def list_users(offset=0, limit=25, order="desc", sort="last_active"):
    if sort == "name":
        users = [model_to_dict(user) for user in User.select().offset(offset).limit(limit).order_by(User.name.asc() if order == "asc" else User.name.desc())]
    else:
        users = [model_to_dict(user) for user in User.select().offset(offset).limit(limit).order_by(User.last_active.asc() if order == "asc" else User.last_active.desc())]
    response = {
        "data": users,
        "_total": User.select().count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return response 

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    user = User.get_or_none(User.id == user_id)
    return model_to_dict(user) if user else {"error": "Not found"}

@app.get("/api/users/{user_id}/games")
def get_user_games(user_id: int, offset=0, limit=25, order="desc", sort="recency"):
    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get ALL activity for the user, joined with games
    activities = Activity.select().where(Activity.user == user).join(Game)

    # Sum up playtimes for each game
    playtimes = {}
    for activity in activities:
        if activity.game.id not in playtimes:
            playtimes[activity.game.id] = {
                "game": model_to_dict(activity.game),
                "seconds": 0,
                "last_played": activity.timestamp
            }
        playtimes[activity.game.id]["seconds"] += activity.seconds
        if activity.timestamp > playtimes[activity.game.id]["last_played"]:
            playtimes[activity.game.id]["last_played"] = activity.timestamp
    
    # Convert playtimes to a list and sort  
    games = list(playtimes.values())
    if sort == "name":
        games.sort(key=lambda x: x["game"]["name"].lower(), reverse=(order == "desc"))
    elif sort == "playtime":
        games.sort(key=lambda x: x["seconds"], reverse=(order == "desc"))
    else:  # recency
        games.sort(key=lambda x: x["last_played"], reverse=(order == "desc"))

    # Now move the games out of the "game" key and add user playtime and last played,
    # and also use limit/offset
    games = games[int(offset) : int(offset) + int(limit)] # Not sure why the int()'s are needed...
    games2 = []
    for game in games:
        game_data = game["game"]
        game_data["seconds_played"] = game["seconds"]
        game_data["last_played"] = game["last_played"]
        games2.append(game_data)

    response = {
        "data": games2,
        "_total": activities.distinct(Activity.game).count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return response

@app.get("/api/users/{user_id}/stats")
def get_user_stats(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    oldest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.asc()).first()
    newest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).first()
    total_playtime = Activity.select(fn.SUM(Activity.seconds)).where(Activity.user == user).scalar() or 0
    total_activities = Activity.select().where(Activity.user == user).count()
    total_games = Activity.select(Activity.game).where(Activity.user == user).distinct().count()
    total_platforms = Activity.select(Activity.platform).where(Activity.user == user).distinct().count()

    return {
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
    }

@app.get("/api/activities")
def list_activities(offset = 0, limit = 25, order = "desc", user: int | None = None, game: int | None = None, platform: int | None = None):
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
    return response


@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int):
    activity = Activity.get_or_none(Activity.id == activity_id) # type: ignore
    return model_to_dict(activity) if activity else {"error": "Not found"}

@app.get("/api/games")
def list_games(offset=0, limit=25, order="desc", sort="recency"):
    # recency | playtime | name
    if sort == "name":
        games = [model_to_dict(game) for game in Game.select().where(Game.seconds_played > 0).offset(offset).limit(limit).order_by(Game.name.asc() if order == "asc" else Game.name.desc())] # type: ignore
    elif sort == "playtime":
        games = [model_to_dict(game) for game in Game.select().where(Game.seconds_played > 0).offset(offset).limit(limit).order_by(Game.seconds_played.asc() if order == "asc" else Game.seconds_played.desc())] # type: ignore
    else: #elif sort == "recency": 
        games = [model_to_dict(game) for game in Game.select().where(Game.seconds_played > 0).offset(offset).limit(limit).order_by(Game.last_played.asc() if order == "asc" else Game.last_played.desc())] # type: ignore

    response = {
        "data": games,
        "_total": Game.select().count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return response

@app.get("/api/games/{game_id}")
def get_game(game_id: int):
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return model_to_dict(game)

# @app.get("/api/games/{game_id}/stats")
# def get_game_stats(game_id: int):
#     game = Game.get_or_none(Game.id == game_id) # type: ignore
#     if not game:
#         raise HTTPException(status_code=404, detail="Game not found")

#     total_playtime = game.seconds_played
#     total_activities = Activity.select().where(Activity.game == game).count()
#     total_users = Activity.select(Activity.user).where(Activity.game == game).distinct().count()
#     played_platforms = Activity.select(Activity.platform).where(Activity.game == game).distinct()
#     platform_count = played_platforms.count()
#     last_activity = game.last_played
    
#     platforms = [model_to_dict(platform.platform) for platform in played_platforms]

#     return {
#         "total": {
#             "seconds": total_playtime,
#             "activities": total_activities,
#             "users": total_users,
#             "platforms": platform_count
#         },
#         "last_activity": model_to_dict(last_activity) if last_activity else None,
#         "platforms": platforms,
#         "average": {
#             "seconds_per_user": total_playtime / total_users if total_users > 0 else 0,
#             "sessions_per_user": total_activities / total_users if (total_activities > 0 and total_users > 0) else 0,
#             "session_length": total_playtime / total_activities if (total_activities > 0 and total_playtime > 0) else 0,
#         }
#     }

@app.get("/api/platforms")
def list_platforms(offset=0, limit=25, order="desc"):
    platforms = [model_to_dict(platform) for platform in Platform.select().offset(offset).limit(limit).order_by(Platform.abbreviation.asc() if order == "asc" else Platform.abbreviation.desc())]

    response = {
        "data": platforms,
        "_total": Platform.select().count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return response

@app.get("/api/platforms/{platform_id}")
def get_platform(platform_id: int):
    platform = Platform.get_or_none(Platform.id == platform_id) # type: ignore
    return model_to_dict(platform) if platform else {"error": "Not found"}

@app.get("/api/stats")
def get_stats():
    total_users = User.select().count()
    total_games = Activity.select(Activity.game).distinct().count() # Only get games with activity
    total_activities = Activity.select().count()
    total_platforms = Platform.select().count()
    total_playtime = Activity.select(fn.SUM(Activity.seconds)).scalar() or 0

    return {
        "total": {
            "seconds": total_playtime,
            "users": total_users,
            "games": total_games,
            "activities": total_activities,
            "platforms": total_platforms
        }
    }

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