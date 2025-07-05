import datetime
import logging

from oblivionis import utils
from oblivionis.storage.storage_v2 import User, Game, Platform, Activity
from oblivionis.consts import MINIMUM_SESSION_LENGTH

logger = logging.getLogger("operations")
    
def get_game_by_alias(alias: str) -> Game | None:
    """
    Returns a game by its alias.
    If no game is found, returns None.
    """
    return Game.get_or_none(Game.aliases.contains(alias))

def add_session(user: User, game: Game, seconds: int, platform:Platform|None=None, timestamp:datetime.datetime|None=None) -> tuple[Activity|None, Exception|None]:
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

        activity = Activity.create(user=user, game=game, seconds=seconds, platform=platform, timestamp=timestamp)

        logger.info("Added activity %s for user %s: %s (%s) - %s seconds @ %s",
                    activity.id, user, game, platform, seconds, timestamp.isoformat())
    
        
        return activity, None
    except Exception as e:
        logger.error("Failed to add session for user %s: %s", user.id, e)
        return None, e
    
def remove_game_images(game:Game) -> str:    
    Game.update(small_image=None, large_image=None).where(Game.id == game.id).execute() # type: ignore
    logger.info("Removed images for game %s", game.name)
    return f"Images for game '{game.name}' removed successfully."

def remove_session(user: User, sessionId: int):
    activity = Activity.get_or_none(Activity.id == sessionId) # type: ignore
    if not activity:
        return f"ERROR: Session {sessionId} not found"
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.delete_instance()
    return f"Session {sessionId} removed successfully."

def merge_games(user: User, gameId1: int, gameId2: int):
    game1 = Game.get_or_none(Game.id == gameId1) # type: ignore
    if not game1:
        return f"ERROR: Game with ID {gameId1} not found"
    game2 = Game.get_or_none(Game.id == gameId2) # type: ignore
    if not game2:
        return f"ERROR: Game with ID {gameId2} not found"
    Activity.update(game=game2).where(
        (Activity.game == game1) & (Activity.user == user)
    ).execute()
    return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"



def set_default_platform(user: User, platform: str) -> str:
    user.default_platform = platform # type: ignore
    user.save()
    return f"Your default platform is now **{user.default_platform}**"
    
def set_platform_for_session(user: User, sessionId: int, platform: Platform) -> bool:
    activity = Activity.get_or_none(Activity.id == sessionId) # type: ignore
    if not activity:
        return False
    if activity.user.id != user.id:
        return False
    activity.platform = platform
    activity.save()
    return True

def modify_session_date(user: User, sessionId: int, new_date: datetime.datetime) -> str:
    activity = Activity.get_or_none(Activity.id == sessionId) # type: ignore
    if not activity:
        return f"ERROR: Session {sessionId} not found"
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.timestamp = new_date
    activity.save()
    return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')} UTC"
