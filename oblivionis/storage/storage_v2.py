import os
import logging

from oblivionis import utils
from oblivionis.storage.reset_sequence import reset_sequences

DB_NAME="storage_v2"

logger = logging.getLogger("storage_v2")

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
    TextField,
    fn,
)
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField

db = PostgresqlExtDatabase(
    DB_NAME,
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


class BaseModel(Model):
    class Meta:
        database = db

class Platform(BaseModel):
    """
    Platform (V2)
    """
    abbreviation = CharField(unique=True)
    name = CharField(null=True)

class User(BaseModel):
    """
    User (V2)
    """
    id = CharField(primary_key=True)
    name = CharField()
    default_platform = ForeignKeyField(Platform, default=lambda: Platform.get_or_create(abbreviation="pc")[0])
    bot_commands_blocked = BooleanField(default=False)


class Game(BaseModel):
    """
    Game (V2)
    """
    name = CharField(unique=True)
    steam_id = IntegerField(null=True, default=None)
    sgdb_id = IntegerField(null=True, default=None)
    image_url = CharField(null=True, default=None)
    aliases = ArrayField(TextField,  default=[]) # type: ignore
    release_year = IntegerField(null=True, default=None)


class Activity(BaseModel):
    """
    Activity (V2)
    """
    timestamp = DateTimeField()
    user = ForeignKeyField(User, backref='activities')
    game = ForeignKeyField(Game, backref='activities')
    platform = ForeignKeyField(Platform, backref='activities')
    seconds = IntegerField()

class LiveActivity(BaseModel):
    user = ForeignKeyField(User, backref='live_activities')
    game = ForeignKeyField(Game, backref='live_activities')
    platform = ForeignKeyField(Platform, backref='live_activities')
    started = DateTimeField()    

class DiscordHistory(BaseModel):
    timestamp = DateTimeField(default=lambda: utils.now())
    event = TextField()
    user = CharField(null=True)  # Discord user ID if applicable
    message = TextField()

def connect_db():
    if db.connect():
        logger.info("Connected to database %s", DB_NAME)
        db.create_tables([Platform, User, Game, Activity, LiveActivity, DiscordHistory])
        reset_sequences([Platform, Game, Activity, LiveActivity, DiscordHistory])
    
