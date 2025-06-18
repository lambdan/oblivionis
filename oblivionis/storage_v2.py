import datetime
import os
import logging
from oblivionis.globals import LOGLEVEL

logger = logging.getLogger("storage_v2")

from peewee import (
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
    os.environ.get("DB_NAME") + "_2", # type: ignore
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
)


class BaseModel(Model):
    class Meta:
        database = db

class Platform(BaseModel):
    abbreviation = CharField(unique=True)
    name = CharField(null=True)

class User(BaseModel):
    id = CharField(primary_key=True, max_length=20)
    name = CharField()
    default_platform = ForeignKeyField(Platform, default=lambda: Platform.get_or_create(abbreviation="pc")[0])


class Game(BaseModel):
    name = CharField(unique=True)
    steam_id = IntegerField(null=True, default=None)
    sgdb_id = IntegerField(null=True, default=None)
    image_url = CharField(null=True, default=None)
    aliases = ArrayField(TextField,  default=[]) # type: ignore
    release_year = IntegerField(null=True, default=None)


class Activity(BaseModel):
    timestamp = DateTimeField()
    user = ForeignKeyField(User)
    game = ForeignKeyField(Game)
    seconds = IntegerField()
    platform = ForeignKeyField(Platform)


def connect_db():
    db.connect()
    db.create_tables([Platform, User, Game, Activity])
   