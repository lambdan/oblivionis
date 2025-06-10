import datetime
import logging
import os

import discord
from discord.ext import commands

from oblivionis import storage
from oblivionis.commands import dm_receive
from oblivionis.operations import add_session

logger = logging.getLogger("bot.py")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def game_from_activity(activity) -> str:
    if activity.name == "Steam Deck":
        return activity.details.removeprefix("Playing ")
    return activity.name

def platform_from_activity(activity) -> str:
    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Game.platform
    logger.debug("platform_from_activity: %s %s", activity.name, activity.platform)
    if activity.name == "Steam Deck":
        return "steam-deck"
    try:
        if activity.platform:
            return activity.platform.lower()
    except Exception as e:
        logger.warning("Failed to get platform from activity %s %s %s", activity.name, activity.platform, e)
    return "pc"

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
        seconds = int(duration.total_seconds())
        game = game_from_activity(activity)
        platform = platform_from_activity(activity)
        logger.info("%s has stopped playing %s on %s after %s seconds", before, game, platform, seconds)
        add_session(
            userId=before.id,
            userName=before.name,
            gameName=game,
            seconds=seconds,
            platform=platform,
        )
    elif after.activity.type == discord.ActivityType.playing:
        game = game_from_activity(after.activity)
        platform = platform_from_activity(after.activity)
        logger.info("%s has started playing %s on %s", after, game, platform)


@bot.event
async def on_ready():
    logger.info("Oblivionis is ready")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    logger.debug("Received message from %s: %s", message.author, message.content)
    reply = dm_receive(message)
    logger.debug("Replying to %s: %s", message.author, reply)
    await message.author.send(reply)

def main():
    storage.connect_db()
    bot.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
