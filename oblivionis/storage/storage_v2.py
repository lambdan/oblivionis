import datetime
import http
import os
import logging
import uuid
from oblivionis.globals import LOGLEVEL

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
    last_played = DateTimeField(null=True, default=None)
    seconds_played = IntegerField(default=0)

class User(BaseModel):
    """
    User (V2)
    """
    id = CharField(primary_key=True)
    name = CharField()
    avatar_url = CharField(null=True)
    last_active = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    seconds_played = IntegerField(default=0)
    default_platform = ForeignKeyField(Platform, default=lambda: Platform.get_or_create(abbreviation="pc")[0])


class Game(BaseModel):
    """
    Game (V2)
    """
    name = CharField(unique=True)
    last_played = DateTimeField(null=True, default=None)
    seconds_played = IntegerField(default=0)
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
    

def connect_db():
    if db.connect():
        logger.info("Connected to database %s", DB_NAME)
        db.create_tables([Platform, User, Game, Activity])
    
def sync_totals():
    """
    Sync total playtime and activity counts for users and games
    """
    if db.is_closed():
        logger.error("Database connection is closed. Cannot sync totals.")
        return

    logger.info("Syncing totals for users and games")
    started = datetime.datetime.now(datetime.UTC)
    
    # Update total seconds played for each user
    for user in User.select():
        total_seconds = Activity.select(fn.SUM(Activity.seconds)).where(Activity.user == user).scalar() or 0
        user.seconds_played = total_seconds
        user.save()
    
    # Update total seconds played for each game
    for game in Game.select():
        total_seconds = Activity.select(fn.SUM(Activity.seconds)).where(Activity.game == game).scalar() or 0
        game.seconds_played = total_seconds
        game.save()

    # Sync last played timestamps
    for game in Game.select():
        last_activity = Activity.select().where(Activity.game == game).order_by(Activity.timestamp.desc()).first()
        if last_activity:
            game.last_played = last_activity.timestamp
            game.save()
    
    # Sync last active timestamps for users
    for user in User.select():
        last_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).first()
        if last_activity:
            user.last_active = last_activity.timestamp
            user.save()

    # Update last played and seconds played for platforms
    for platform in Platform.select():
        total_seconds = Activity.select(fn.SUM(Activity.seconds)).where(Activity.platform == platform).scalar() or 0
        platform.seconds_played = total_seconds
        
        last_activity = Activity.select().where(Activity.platform == platform).order_by(Activity.timestamp.desc()).first()
        if last_activity:
            platform.last_played = last_activity.timestamp
        
        platform.save()
    
    logger.info("Sync complete, took %s seconds", (datetime.datetime.now(datetime.UTC) - started).total_seconds())
