import datetime
import os
import logging
from oblivionis.globals import LOGLEVEL

logger = logging.getLogger("storage")

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
    id = IntegerField(primary_key=True)
    name = CharField(unique=True)
    steam_id = IntegerField(null=True, default=None)
    sgdb_id = IntegerField(null=True, default=None)
    image_url = CharField(null=True, default=None)


class Activity(BaseModel):
    id = IntegerField(primary_key=True)
    timestamp = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    seconds = IntegerField()
    platform = CharField(default="pc", max_length=20)
    

def game_from_id(gameId: int) -> Game | None:
    return Game.get_or_none(Game.id == gameId)
    
def game_from_name(gameName: str) -> Game | None:
    return Game.get_or_none(Game.name == gameName)

def activity_from_id(sessionId: int) -> Activity | None:
    return Activity.get_or_none(Activity.id == sessionId)

def user_from_id(userId: str) -> User | None:
    return User.get_or_none(User.id == userId)

def connect_db():
    if db.connect():
        logger.info("Connected to database %s", db.database)
    db.create_tables([User, Game, Activity])
    with db.atomic():
        ##############
        # Evolutions #
        ##############
        # Add platform column if it doesn't exist
        db.execute_sql("ALTER TABLE public.activity ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'pc';")
        # Add default_platform column to User if it doesn't exist
        db.execute_sql("ALTER TABLE public.user ADD COLUMN IF NOT EXISTS default_platform VARCHAR(20) DEFAULT 'pc';")
        # Add small_image and large_image columns to Game if they don't exist
        db.execute_sql("ALTER TABLE public.game ADD COLUMN IF NOT EXISTS small_image VARCHAR(255);")
        db.execute_sql("ALTER TABLE public.game ADD COLUMN IF NOT EXISTS large_image VARCHAR(255);")
        # Add steam_id column
        db.execute_sql("ALTER TABLE public.game ADD COLUMN IF NOT EXISTS steam_id INTEGER;")
        # Add sgdb_id column
        db.execute_sql("ALTER TABLE public.game ADD COLUMN IF NOT EXISTS sgdb_id INTEGER;")
        # Delete old small and large image columns
        db.execute_sql("ALTER TABLE public.game DROP COLUMN IF EXISTS small_image;")
        db.execute_sql("ALTER TABLE public.game DROP COLUMN IF EXISTS large_image;")
        # Add image_url column
        db.execute_sql("ALTER TABLE public.game ADD COLUMN IF NOT EXISTS image_url VARCHAR(255);")
        