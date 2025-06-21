import datetime
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
    
class Token(BaseModel):
    """
    API Token (V2)
    """
    token = CharField(unique=True, default=lambda: str(uuid.uuid4()))
    user = ForeignKeyField(User, backref='tokens') # Who requested the token
    created_at = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    expires_at = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))  # Default to 1 year
    super = BooleanField(default=False)  # Super token has all permissions, and always will
    discordAccess = BooleanField(default=False)
    sgdbAccess = BooleanField(default=False)

def connect_db():
    if db.connect():
        logger.info("Connected to database %s", DB_NAME)
        db.create_tables([Platform, User, Game, Activity, Token])
    
