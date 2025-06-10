import datetime
import os
import logging
logger = logging.getLogger("storage.py")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
