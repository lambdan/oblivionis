import os, logging, datetime
import discord
from discord.ext import commands
from oblivionis import storage
from oblivionis.commands import dm_receive
from oblivionis.operations import add_session, get_or_create_user
from oblivionis.globals import DEBUG, LOGLEVEL

if DEBUG:
    print("**************************")
    print("*** DEBUG MODE ENABLED ***")
    print("**************************")

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def game_from_activity(activity: discord.Activity) -> str | None:
    if activity.name and activity.details:
        logger.info("DEBUG game_from_activity: %s , %s", activity.name, activity.details)

    if activity.name == "Steam Deck" and activity.details:
        return activity.details.removeprefix("Playing ")
    return activity.name

def platform_from_activity(activity: discord.Activity) -> str:
    # https://discordpy.readthedocs.io/en/stable/api.html#discord.Game.platform
    if activity.name == "Steam Deck":
        return "steam-deck"
    try:
        if activity.platform:
            return activity.platform.lower()
    except Exception as e:
        logger.warning("Failed to get platform from activity %s %s %s", activity.name, activity.platform, e)
    return "pc"

@bot.event
async def on_guild_available(guild: discord.Guild):
    logger.info("Server %s available", guild)


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    logger.debug("User presence changed")

    if after.activity == before.activity or before.activity is None:
        return

    if after.activity is None and before.activity.type == discord.ActivityType.playing:
        activity: discord.Activity = before.activity # type: ignore
        duration = datetime.datetime.now(datetime.UTC) - activity.start # type: ignore
        seconds = int(duration.total_seconds())

        game = game_from_activity(activity)
        if not game:
            logger.warning("No game found in activity %s", activity)
            return
        
        user = get_or_create_user(str(before.id), before.name)
        if not user:
            return
        
        platform = platform_from_activity(activity)
        logger.info("%s has stopped playing %s on %s after %s seconds", before, game, platform, seconds)
        add_session(
            user=user,
            gameName=game,
            seconds=seconds,
            platform=platform,
        )
    elif after.activity and after.activity.type == discord.ActivityType.playing:
        activity: discord.Activity = after.activity # type: ignore
        game = game_from_activity(activity)
        platform = platform_from_activity(activity)
        logger.info("%s has started playing %s on %s", after, game, platform)


@bot.event
async def on_ready():
    logger.info("Oblivionis is ready")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    # ! in prod
    # !! while developing
    if message.content.startswith("!!"):
        if not DEBUG:
            return
        message.content = message.content[1:]

    try:
        logger.info("Received message from %s: %s", message.author, message.content)
        reply = dm_receive(message)
        logger.info("Replying to %s: %s", message.author, reply)
        await message.author.send(reply)
    except Exception as e:
        logger.error("Error processing message from %s: %s", message.author, e)
        await message.author.send(f"Error: {e}")

def main():
    storage.connect_db()
    bot.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
