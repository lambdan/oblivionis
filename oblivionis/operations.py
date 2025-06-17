import datetime
import logging

from oblivionis import storage, utils
from oblivionis.models import ActivityAssets
from oblivionis.storage import User, Game, Activity
from oblivionis.consts import MINIMUM_SESSION_LENGTH

logger = logging.getLogger("operations")

def get_or_create_user(userId: str, userName: str) -> storage.User | None:
    try:
        user, user_created = storage.User.get_or_create(id=userId, defaults={"name": userName})
        if user_created:
            logger.info("Added new user %s %s to database", userId, userName)
        logger.debug("Returning user %s", user)
        return user
    except Exception as e:
        logger.error("Failed to get or create user %s: %s", userId, e)
        return None

def get_or_create_game(gameName: str) -> storage.Game | None:
    try:
        game, game_created = storage.Game.get_or_create(name=gameName)
        if game_created:
            logger.info("Added new game %s to database", gameName)
        logger.debug("Returning game %s", game)
        return game
    except Exception as e:
        logger.error("Failed to get or create game %s: %s", gameName, e)
        return None
    
def get_game_by_alias(alias: str) -> storage.Game | None:
    """
    Returns a game by its alias.
    If no game is found, returns None.
    """
    try:
        game = storage.Game.get(storage.Game.aliases.contains(alias))
        logger.debug("Found game by alias '%s': %s %s", alias, game.id, game.name)
        return game
    except Exception as e:
        logger.debug("Did not get game by alias '%s': %s", alias, e)
        return None

def add_session(user: storage.User, gameName: str, seconds: int, platform:str|None=None, timestamp:datetime.datetime|None=None) -> tuple[Activity|None, Exception|None]:
    """
    Adds a new session to the database.
    Returns a tuple of (Activity, None) on success, or (None, Exception) on failure.
    """
    if seconds < MINIMUM_SESSION_LENGTH:
        return None, ValueError("Session must be at least {MINIMUM_SESSION_LENGTH} seconds long")
    
    try:
        if platform is None: # Use default platform if not provided
            platform = str(user.default_platform)

        if timestamp is None: # Use current time if not provided
            timestamp = utils.now()

        game = get_or_create_game(gameName)
        if not game:
            return None, Exception(f"Game '{gameName}' not found or could not be created")

        activity = storage.Activity.create(user=user, game=game, seconds=seconds, platform=platform, timestamp=timestamp)

        logger.info("Added activity %s for user %s: %s (%s) - %s seconds @ %s",
                    activity.id, user, gameName, platform, seconds, timestamp.isoformat())
        
        return activity, None
    except Exception as e:
        logger.error("Failed to add session for user %s: %s", user.id, e)
        return None, e
    
def remove_game_images(game: storage.Game) -> str:    
    Game.update(small_image=None, large_image=None).where(Game.id == game.id).execute()
    logger.info("Removed images for game %s", game.name)
    return f"Images for game '{game.name}' removed successfully."

def remove_session(user: storage.User, sessionId: int):
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.delete_instance()
    return f"Session {sessionId} removed successfully."

def merge_games(user: storage.User, gameId1: int, gameId2: int):
    game1 = Game.get(Game.id == gameId1)
    game2 = Game.get(Game.id == gameId2)
    Activity.update(game=game2).where(
        (Activity.game == game1) & (Activity.user == user)
    ).execute()
    return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"

def set_game_for_activity(activity: storage.Activity, newGame: storage.Game) -> str:
    if activity.game == newGame:
        return f"Activity {activity.id} is already set to game {newGame.name}"
    oldGame = activity.game
    Activity.update(game=newGame).where(Activity.id == activity.id).execute()
    return f"Activity {activity.id} has been changed from **{oldGame} to game **{newGame.name}**"

def set_default_platform(user: storage.User, platform: str) -> str:
    user.default_platform = platform # type: ignore
    user.save()
    return f"Your default platform is now **{user.default_platform}**"
    
def set_platform_for_session(user: storage.User, sessionId: int, platform: str) -> str:
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.platform = platform
    activity.save()
    return f"Platform for **{activity}** has been set to **{platform}**"

def modify_session_date(user: storage.User, sessionId: int, new_date: datetime.datetime) -> str:
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.timestamp = new_date
    activity.save()
    return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')} UTC"
