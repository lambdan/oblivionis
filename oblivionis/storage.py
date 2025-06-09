import os
import logging
logger = logging.getLogger("storage.py")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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


class Game(BaseModel):
    name = CharField(unique=True)


class Activity(BaseModel):
    timestamp = DateTimeField()
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    seconds = IntegerField()
    platform = CharField(default="pc", max_length=20)


def connect_db():
    db.connect()
    db.create_tables([User, Game, Activity])
    # Add platform column if it doesn't exist
    db.execute_sql("ALTER TABLE activity ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'pc';")


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
