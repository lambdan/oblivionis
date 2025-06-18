import datetime
import logging

from oblivionis import utils
from oblivionis.models import ActivityAssets
from oblivionis.storage import storage_v2
from oblivionis.consts import MINIMUM_SESSION_LENGTH

logger = logging.getLogger("operations")

def get_or_create_user(userId: str, userName: str) -> storage_v2.User | None:
    try:
        user, user_created = storage_v2.User.get_or_create(id=userId, defaults={"name": userName})
        if user_created:
            logger.info("Added new user %s %s to database", userId, userName)
        logger.debug("Returning user %s", user)
        return user
    except Exception as e:
        logger.error("Failed to get or create user %s: %s", userId, e)
        return None

def get_or_create_game(gameName: str) -> storage_v2.Game | None:
    try:
        game, game_created = storage_v2.Game.get_or_create(name=gameName)
        if game_created:
            logger.info("Added new game %s to database", gameName)
        logger.debug("Returning game %s", game)
        return game
    except Exception as e:
        logger.error("Failed to get or create game %s: %s", gameName, e)
        return None
    
def get_game_by_alias(alias: str) -> storage_v2.Game | None:
    """
    Returns a game by its alias.
    If no game is found, returns None.
    """
    try:
        game = storage_v2.Game.get(storage_v2.Game.aliases.contains(alias))
        logger.debug("Found game by alias '%s': %s %s", alias, game.id, game.name)
        return game
    except Exception as e:
        logger.debug("Did not get game by alias '%s': %s", alias, e)
        return None

def add_session(user: storage_v2.User, game: storage_v2.Game, seconds: int, platform:storage_v2.Platform|None=None, timestamp:datetime.datetime|None=None) -> tuple[storage_v2.Activity|None, Exception|None]:
    """
    Adds a new session to the database.
    Returns a tuple of (Activity, None) on success, or (None, Exception) on failure.
    """
    if seconds < MINIMUM_SESSION_LENGTH:
        return None, ValueError("Session must be at least {MINIMUM_SESSION_LENGTH} seconds long")
    
    try:
        if platform is None: # Use default platform if not provided
            platform = user.default_platform # type: ignore

        if timestamp is None: # Use current time if not provided
            timestamp = utils.now()

        activity = storage_v2.Activity.create(user=user, game=game, seconds=seconds, platform=platform, timestamp=timestamp)

        logger.info("Added activity %s for user %s: %s (%s) - %s seconds @ %s",
                    activity.id, user, game, platform, seconds, timestamp.isoformat())
        
        return activity, None
    except Exception as e:
        logger.error("Failed to add session for user %s: %s", user.id, e)
        return None, e
    
def remove_game_images(game: storage_v2.Game) -> str:    
    storage_v2.Game.update(small_image=None, large_image=None).where(storage_v2.Game == game).execute()
    logger.info("Removed images for game %s", game.name)
    return f"Images for game '{game.name}' removed successfully."

def remove_session(user: storage_v2.User, sessionId: int):
    activity = storage_v2.Activity.get(storage_v2.Activity == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.delete_instance()
    return f"Session {sessionId} removed successfully."

def merge_games(user: storage_v2.User, gameId1: int, gameId2: int):
    game1 = storage_v2.Game.get(storage_v2.Game == gameId1)
    game2 = storage_v2.Game.get(storage_v2.Game == gameId2)
    storage_v2.Activity.update(game=game2).where(
        (storage_v2.Activity.game == game1) & (storage_v2.Activity.user == user)
    ).execute()
    return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"

def set_game_for_activity(activity: storage_v2.Activity, newGame: storage_v2.Game) -> str:
    if activity.game == newGame:
        return f"Activity {activity} is already set to game {newGame}"
    oldGame = activity.game
    storage_v2.Activity.update(game=newGame).where(storage_v2.Activity == activity).execute()
    return f"Activity {activity} has been changed from **{oldGame}** to **{newGame}**"

def set_default_platform(user: storage_v2.User, platform: str) -> str:
    user.default_platform = platform # type: ignore
    user.save()
    return f"Your default platform is now **{user.default_platform}**"
    
def set_platform_for_session(user: storage_v2.User, sessionId: int, platform: str) -> str:
    activity = storage_v2.Activity.get(storage_v2.Activity == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.platform = platform
    activity.save()
    return f"Platform for **{activity}** has been set to **{platform}**"

def modify_session_date(user: storage_v2.User, sessionId: int, new_date: datetime.datetime) -> str:
    activity = storage_v2.Activity.get(storage_v2.Activity == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.timestamp = new_date
    activity.save()
    return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')} UTC"
