import datetime
import logging

from oblivionis import storage, utils
from oblivionis.storage import User, Game, Activity
from oblivionis.consts import VALID_PLATFORMS

logger = logging.getLogger("operations.py")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def add_session(userId: str, userName: str, gameName: str, seconds: int, platform:str=None, timestamp:datetime.datetime= None) -> str:
    if seconds < 30:
        logger.warning("Session for user %s on game %s is less than 30 seconds. Ignoring.", userName, gameName)
        return "Session too short, ignoring."
    
    user, user_created = storage.User.get_or_create(id=userId, defaults={"name": userName})
    if user_created:
        logger.info("Added new user %s %s to database", userName, userId)

    if platform is None:
        # Get the user's default platform if not provided
        platform = user.default_platform

    if timestamp is None:
        timestamp = utils.now()

    game, game_created = storage.Game.get_or_create(name=gameName)
    if game_created:
        logger.info("Added new game '%s' to database", game.name)
    
    storage.Activity.create(user=user, game=game, seconds=seconds, platform=platform, timestamp=timestamp)
    
    msg = f"{userName} played {gameName} for {seconds} seconds"
    logger.info(msg)
    return msg

def remove_session(userId: int, sessionId: int):
    try:
        user = User.get(User.id == userId)
        activity = Activity.get(Activity.id == sessionId)
        if activity.user != user:
            return f"ERROR: Session {sessionId} does not belong to you"
        activity.delete_instance()
        return f"Session {sessionId} removed successfully."
    except User.DoesNotExist:
        return f"ERROR: User {userId} not found"
    except Activity.DoesNotExist:
        return f"ERROR: Session {sessionId} not found"

def merge_games(userId: int, gameId1: int, gameId2: int):
    try:
        game1 = Game.get(Game.id == gameId1)
        game2 = Game.get(Game.id == gameId2)
        user = User.get(User.id == userId)
        
        Activity.update(game=game2).where(
            (Activity.game == game1) & (Activity.user == user)
        ).execute()
        
        return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"
    except User.DoesNotExist:
        return f"ERROR: User {userId} not found"
    except Game.DoesNotExist:
        return f"ERROR: One or both games not found (IDs: {gameId1}, {gameId2})"
    except Exception as e:
        logger.error(f"Unexpected error while merging games: {e}")
        return f"ERROR: An unexpected error occurred while merging games"

def set_default_platform(userId: str, platform: str) -> str:
    try:
        user = User.get(User.id == userId)
        user.default_platform = platform
        user.save()
        return f"Your default platform has been set to **{platform}**"

    except User.DoesNotExist:
        return f"ERROR: User {userId} not found"
    
def set_platform_for_session(userId: str, sessionId: int, platform: str) -> str:
    try:
        user = User.get(User.id == userId)
        activity = Activity.get(Activity.id == sessionId)
        if activity.user != user:
            return f"ERROR: Session {sessionId} does not belong to you"
        activity.platform = platform
        activity.save()
        return f"Platform for session {sessionId} has been set to **{platform}**"
    except User.DoesNotExist:
        return f"ERROR: User {userId} not found"
    except Activity.DoesNotExist:
        return f"ERROR: Session {sessionId} not found"
    
def modify_session_date(userId: str, sessionId: int, new_date: datetime.datetime) -> str:
    try:
        user = User.get(User.id == userId)
        activity = Activity.get(Activity.id == sessionId)
        if activity.user != user:
            return f"ERROR: Session {sessionId} does not belong to you"
        activity.timestamp = new_date
        activity.save()
        return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"ERROR: {str(e)}"