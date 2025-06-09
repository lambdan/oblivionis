import datetime
import logging
import os

import discord
from discord.ext import commands

from oblivionis import storage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def now():
    return datetime.datetime.now(datetime.UTC)

def add_session(userId, userName, gameName, seconds, ts=now()):
    logger.info(
            "%s has played %s for %s seconds at %s",
            userName,
            gameName,
            seconds,
            ts,
        )
    user, user_created = storage.User.get_or_create(id=userId, defaults={"name": userName})
    if user_created:
        logger.info("Added new user %s %s to database", userName, userId)

    game, game_created = storage.Game.get_or_create(name=gameName)
    if game_created:
        logger.info("Added new game '%s' to database", game.name)
    storage.Activity.create(user=user, game=game, seconds=seconds, timestamp=ts)

def game_from_activity(activity) -> str:
    if activity.name == "Steam Deck":
        return activity.details.removeprefix("Playing ")
    return activity.name

@bot.event
async def on_guild_available(guild):
    logger.info("Server %s available", guild)


@bot.event
async def on_presence_update(before, after):
    logger.debug("User presence changed")
    if after.activity == before.activity:
        return

    if after.activity is None and before.activity.type == discord.ActivityType.playing:
        activity = before.activity
        duration = datetime.datetime.now(datetime.UTC) - activity.start
        game_name = game_from_activity(activity)
        add_session(
            userId=before.id,
            userName=before.name,
            gameName=game_name,
            seconds=int(duration.total_seconds()),
        )
    elif after.activity.type == discord.ActivityType.playing:
        logger.info("%s has started playing %s", after, game_from_activity(after.activity))


@bot.event
async def on_ready():
    logger.info("Oblivionis is ready")


def main():
    storage.connect_db()
    bot.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
