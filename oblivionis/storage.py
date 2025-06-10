import datetime
import os
import logging
logger = logging.getLogger("storage.py")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

VALID_PLATFORMS = ["pc", "switch", "switch2", "ps1", "ps2", "ps3", "ps4", "ps5", "xbox", "xbox360", "xboxone", "xboxseries", "steam-deck", "nes", "snes", "n64", "gamecube", "wii", "wiiu", "ds", "3ds", "psp", "vita"]

from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
)

db = PostgresqlDatabase(
    os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = CharField(primary_key=True, max_length=20)
    name = CharField()
    default_platform = CharField(default="pc", max_length=20)


class Game(BaseModel):
    name = CharField(unique=True)


class Activity(BaseModel):
    timestamp = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    seconds = IntegerField()
    platform = CharField(default="pc", max_length=20)


def connect_db():
    db.connect()
    db.create_tables([User, Game, Activity])
    with db.atomic():
        # Add platform column if it doesn't exist
        db.execute_sql("ALTER TABLE public.activity ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'pc';")
        # Add default_platform column to User if it doesn't exist
        db.execute_sql("ALTER TABLE public.user ADD COLUMN IF NOT EXISTS default_platform VARCHAR(20) DEFAULT 'pc';")


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
    if platform not in VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: {', '.join(VALID_PLATFORMS)}"
    
    try:
        user = User.get(User.id == userId)
        user.default_platform = platform
        user.save()
        return f"Your default platform has been set to **{platform}**"

    except User.DoesNotExist:
        return f"ERROR: User {userId} not found"
    
def set_platform_for_session(userId: str, sessionId: int, platform: str) -> str:
    if platform not in VALID_PLATFORMS:
        return f"ERROR: Invalid platform. Valid platforms are: {', '.join(VALID_PLATFORMS)}"
    
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