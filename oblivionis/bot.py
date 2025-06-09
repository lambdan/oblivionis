import datetime
import logging
import os, json

import discord
from discord.ext import commands

from oblivionis import storage
from oblivionis.dm_features import dm_add_session, dm_help, dm_receive, dm_start_session, dm_stop_session

logger = logging.getLogger("bot.py")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)

def add_session(userId: str, userName: str, gameName: str, seconds: int, platform=None, ts=now()) -> str:
    user, user_created = storage.User.get_or_create(id=userId, defaults={"name": userName})
    if user_created:
        logger.info("Added new user %s %s to database", userName, userId)

    if platform is None:
        # Get the user's default platform if not provided
        platform = user.default_platform
    if platform not in storage.VALID_PLATFORMS:
        logger.warning("Invalid platform '%s' for user %s. Defaulting to 'pc'.", platform, userName)
        platform = "pc"

    game, game_created = storage.Game.get_or_create(name=gameName)
    if game_created:
        logger.info("Added new game '%s' to database", game.name)
    storage.Activity.create(user=user, game=game, seconds=seconds, timestamp=ts, platform=platform)
    
    msg = f"{userName} played {gameName} for {seconds} seconds"

    logger.info(msg)
    return msg

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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    logger.info("Received message from %s: %s", message.author, message.content)

    await message.author.send(dm_receive(message))

def main():
    storage.connect_db()
    bot.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
