import os, logging, datetime
import discord
from discord.ext import commands

from oblivionis.storage import migrate_v1_to_v2, storage_v1, storage_v2
from oblivionis.commands import dm_receive
from oblivionis.operations import add_session
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

def game_from_discord_activity(activity: discord.Activity) -> storage_v2.Game:
    gameName = activity.name
    if gameName == "Steam Deck" and activity.details:
        gameName = activity.details.removeprefix("Playing ")
    game, created = storage_v2.Game.get_or_create(name=gameName)
    if created:
        logger.info("Added new game %s to database", gameName)
    return game

def platform_from_discord_activity(activity: discord.Activity) -> storage_v2.Platform:
    if activity.name == "Steam Deck":
        return storage_v2.Platform.get_or_create(abbreviation="steamdeck")[0]
    platformName = activity.platform or "pc"
    return storage_v2.Platform.get_or_create(abbreviation=platformName)[0]

@bot.event
async def on_guild_available(guild: discord.Guild):
    logger.info("Server %s available", guild)


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    logger.debug("User presence changed for %s: %s -> %s", before, before.activity, after.activity)

    if after.activity == before.activity or before.activity is None:
        return

    if after.activity is None and before.activity.type == discord.ActivityType.playing:
        activity: discord.Activity = before.activity # type: ignore
        duration = datetime.datetime.now(datetime.UTC) - activity.start # type: ignore
        seconds = int(duration.total_seconds())

        game = game_from_discord_activity(activity)
        user, created = storage_v2.User.get_or_create(id=str(before.id), name=before.name)
        
        platform = platform_from_discord_activity(activity)
        logger.info("%s has stopped playing %s on %s after %s seconds", before, game, platform, seconds)
        add_session(
            user=user,
            game=game,
            seconds=seconds,
            platform=platform,
        )
    elif after.activity and after.activity.type == discord.ActivityType.playing:
        activity: discord.Activity = after.activity # type: ignore
        game = game_from_discord_activity(activity)
        platform = platform_from_discord_activity(activity)
        logger.info("%s has started playing %s on %s", after, game, platform)


@bot.event
async def on_ready():
    logger.info("Oblivionis is ready")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.guild:
        # Ignore messages in channels
        return
    
    # ! in prod
    # !! while developing
    if message.content.startswith("!!"):
        if not DEBUG:
            return
        message.content = message.content[1:]

    reply = ""

    try:
        logger.info("<%s>: %s", message.author, message.content)
        reply = dm_receive(message)
    except Exception as e:
        logger.error("Error processing message from %s: %s", message.author, e)
        reply = f"ERROR: {e}"
    
    logger.info("Replying to %s: %s", message.author, reply)
    await message.author.send(reply, reference=message)

def main():
    storage_v1.connect_db()
    storage_v2.connect_db()
    migrate_v1_to_v2.migrate()
    storage_v1.disconnect_db()
    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
