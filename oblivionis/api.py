from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict

from oblivionis import steamgriddb
from oblivionis.storage.storage_v2 import User, Game, Platform, Activity

app = FastAPI()

@app.get("/api/users")
def list_users(offset=0, limit=25, order="desc"):
    users = [model_to_dict(user) for user in User.select().offset(offset).limit(limit).order_by(User.id.asc() if order == "asc" else User.id.desc())]
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

@app.get("/api/activities")
def list_activities(offset = 0, limit = 25, order = "desc", user: int | None = None, game: int | None = None, platform: int | None = None):
    activities = [model_to_dict(activity) for activity in 
        Activity.select().offset(offset).limit(limit).order_by(Activity.timestamp.desc() if order == "desc" else Activity.timestamp.asc())
        .where(
            (Activity.user == user) if user is not None else True,
            (Activity.game == game) if game is not None else True,
            (Activity.platform == platform) if platform is not None else True
        )]
    # convert timestamps to ints
    for activity in activities:
        activity['timestamp'] = int(activity['timestamp'].timestamp()) * 1000
    response = {
        "data": activities,
        "_total": Activity.select().count(),
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
def list_games(offset=0, limit=25, order="desc"):
    games = [model_to_dict(game) for game in Game.select().offset(offset).limit(limit).order_by(Game.name.asc() if order == "asc" else Game.name.desc())]

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
    return model_to_dict(game) if game else {"error": "Not found"}

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