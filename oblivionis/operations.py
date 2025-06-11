import datetime
import logging

from oblivionis import storage, utils
from oblivionis.storage import User, Game, Activity
from oblivionis.consts import VALID_PLATFORMS

logger = logging.getLogger("operations.py")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def game_from_id(gameId: int) -> Game | None:
    return Game.get_or_none(Game.id == gameId)
    
def game_from_name(gameName: str) -> Game | None:
    return Game.get_or_none(Game.name == gameName)

def activity_from_id(sessionId: int) -> Activity | None:
    return Activity.get_or_none(Activity.id == sessionId)

def user_from_id(userId: str) -> User | None:
    return User.get_or_none(User.id == userId)

def add_session(userId: str, userName: str, gameName: str, seconds: int, platform:str|None=None, timestamp:datetime.datetime|None=None) -> str:
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
    
    msg = f"{userName} played {gameName} ({platform}) for {utils.secsToHHMMSS(seconds)} at {timestamp.isoformat()}"
    logger.info(msg)
    return msg

def remove_session(userId: int, sessionId: int):
    user = User.get_or_none(User.id == userId)
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.delete_instance()
    return f"Session {sessionId} removed successfully."

def merge_games(userId: int, gameId1: int, gameId2: int):
    game1 = Game.get(Game.id == gameId1)
    game2 = Game.get(Game.id == gameId2)
    user = User.get(User.id == userId)
    Activity.update(game=game2).where(
        (Activity.game == game1) & (Activity.user == user)
    ).execute()
    return f"Game '{game1.name}' merged into '{game2.name}' successfully for your user"

def set_default_platform(userId: str, platform: str) -> str:
    user = User.get(User.id == userId)
    user.default_platform = platform
    user.save()
    return f"Your default platform has been set to **{platform}**"
    
def set_platform_for_session(userId: str, sessionId: int, platform: str) -> str:
    user = User.get(User.id == userId)
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.platform = platform
    activity.save()
    return f"Platform for session {sessionId} has been set to **{platform}**"

def modify_session_date(userId: str, sessionId: int, new_date: datetime.datetime) -> str:
    user = User.get(User.id == userId)
    activity = Activity.get(Activity.id == sessionId)
    if activity.user != user:
        return f"ERROR: Session {sessionId} does not belong to you"
    activity.timestamp = new_date
    activity.save()
    return f"Session {sessionId} date has been modified to {new_date.strftime('%Y-%m-%d %H:%M:%S')}"
    
