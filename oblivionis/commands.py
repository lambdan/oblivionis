import logging
import os
import re

import discord
from oblivionis import operations, utils, storage, consts
from typing import TypedDict, Dict
import datetime

from oblivionis.globals import ADMINS

logger = logging.getLogger("commands")

def dm_help(isAdmin: bool) -> str:
    base = """
# Help:
- `!help` - Show this message

# Manual addition:
- `!add "Game Name" <duration> [datetime]` - Add a session of specified duration
    - If datetime is not provided, current time is used
        - If datetime is provided, it should be in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)

# Manual start/stop:
- `!start "Game Name"` - Start a manual session
- `!stop` - Stop the current manually started session

# Sessions:
- `!last [n]` - Shows your last n sessions (default is 1, max is 10)

# Maintenance:
- `!merge <game_id1> <game_id2>` - Merge game_id1 into game_id2
- `!remove <session_id>` - Remove session with id

## Date:
- `!setdate <session_id> <datetime>` - Modify the date of a session. Date should be in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)

## Platform: 
- `!setplatform <session_id> <platform>` - Set the platform for a specific session
- `!setplatform <session_id1-session_id2> <platform>` - Set the platform for a range of sessions (e.g. `!setplatform 123-456 steam-deck`)

## Game:
- `!game <game_id|game_name>` - Show information about a game
- `!setgame <session_id> "Game Name"` - Change the game of a specific session
    - This is useful if your session shows up as an emulator, and you would like to change it to the actual game you played
- `!setgame <session_id1-session_id2> "Game Name"` - Change the game for a range of sessions (e.g. `!setgame 123-456 "New Game"`)

# Platform:
- `!platform` - Show your current default platform
- `!platform <name>` - Set your default platform
    - This is the platform used when platform cannot be automatically determined (e.g. manual sessions)
- `!listplatforms` - List all valid platforms
"""
    admin = """
# ☢️ Admin commands:
- `!setgameimage <game_id> <url>`
- `!removegameimages <game_id>`
- `!setsteamid <game_id> <steam_id>`
- `!setsgdbid <game_id> <sgdb_id>`
"""
    if isAdmin:
        return base + admin
    return base

class ManualSession(TypedDict):
    gameName: str
    platform: str | None
    startTime: datetime.datetime

MANUAL_SESSIONS: dict[str, ManualSession] = {}

def user_from_message(message: discord.Message, create=False) -> storage.User | None:
    if message.author is None:
        return None
    userId = str(message.author.id)
    if create:
        return operations.get_or_create_user(userId=userId, userName=message.author.name)
    return storage.User.get_or_none(id=userId)

def user_name_from_message(message: discord.Message) -> str:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.name

def dm_add_session(user: storage.User, message: str) -> str:
    # !add "Game Name" <duration> [timestamp]
    message = message.removeprefix('!add "')
    gameName = message.split('"')[0].strip()

    parts = message.split('"')[1].split()
    timestamp = None
    duration = None
    last = parts.pop() # This is the timestamp if provided
    if last.upper().endswith("Z"):
        timestamp = utils.datetimeFromISO8601(last)
        duration = utils.secsFromString(parts.pop())
    else:
        duration = utils.secsFromString(last)

    if duration is None:
        return "ERROR: Duration is invalid"
    
    result = operations.add_session(
                    user=user,
                    gameName=gameName,
                    seconds=duration, timestamp=timestamp)
    sesh = result[0]
    if sesh:
        return f"Session #{sesh.id} saved"
    return f"ERROR: {result[1]}"

def dm_start_session(user: storage.User, message: discord.Message) -> str:
    # !start "Game Name"
    # !start "Game Name" <platform>
    userId = str(user.id)
    if userId in MANUAL_SESSIONS:
        return 'You already have a manual session running. Please `!stop` before starting a new one.'

    msg = message.content.strip()
    msg = msg.removeprefix('!start "').strip()

    gameName = msg.split('"')[0].strip()
    platform = None
    if msg.endswith('"'):
        # If the message ends with a quote, it means no platform is specified
        pass
    else:
        # Platform is specified after the game name
        platform = msg.split('"')[1].strip().lower()
    
    if platform and not platform in consts.VALID_PLATFORMS:
        return "ERROR: Invalid platform"
    
    if platform is None:
        platform = str(user.default_platform)

    MANUAL_SESSIONS[userId] = {
        "gameName": gameName,
        "platform": platform,
        "startTime": utils.now()
    }
    return f"You have started playing **{gameName}** on **{platform}**.\nSend `!stop` to end the session."

def dm_stop_session(user: storage.User, message: discord.Message) -> str:
    # !stop
    userId = str(user.id)
    if userId not in MANUAL_SESSIONS:
        return "You don't have a manual session running"
    
    session = MANUAL_SESSIONS.pop(userId)
    gameName = session["gameName"]
    startTime = session["startTime"]
    duration = utils.now() - startTime
    seconds = int(duration.total_seconds())
    result = operations.add_session(
                user=user,
                platform=session["platform"],
                gameName=gameName,
                seconds=seconds)
    
    sesh = result[0]
    if sesh:
        return f"Session #{sesh} saved.\nYou played **{gameName}** on **{sesh.platform}** for {utils.secsToHHMMSS(int(str(sesh.seconds)))}"
    
    if isinstance(result[1], ValueError):
        return "Session ended, but not saved because it was too short"
    # internal failure
    MANUAL_SESSIONS[userId] = session
    return f"ERROR: Could not save session. Your session will keep running. Please try again."
    

def dm_merge_game(user: storage.User, message: discord.Message) -> str:
    # !merge 123 456 # Merge game with ID 123 into game with ID 456
    parts = message.content[7:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!merge game_id1 game_id2`"
    try:
        game_id1 = int(parts[0])
        game_id2 = int(parts[1])
    except ValueError:
        return "Invalid game IDs. Please provide valid integers."
    return operations.merge_games(user, gameId1=game_id1, gameId2=game_id2)

def dm_remove_session(user: storage.User, message: discord.Message) -> str:
    # !remove session_id
    parts = message.content[8:].split()
    if len(parts) != 1:
        return "Invalid command format. Use: `!remove session_id`"
    
    try:
        session_id = int(parts[0])
    except ValueError:
        return "Invalid session ID"
    
    return operations.remove_session(user, sessionId=session_id)

def dm_platform(user: storage.User, message: discord.Message) -> str:
    if message.content == "!platform":
        return f"Your default platform is **{user.default_platform}**. Use `!platform <name>` to change it."
    
    parts = message.content[10:].split()
    if len(parts) != 1:
        return "Invalid command format. Use: `!platform <name>`"
    
    platform = parts[0].lower()
    if platform not in consts.VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(consts.VALID_PLATFORMS)}`"
    
    return operations.set_default_platform(user, platform)

def dm_set_platform(user: storage.User, message: discord.Message) -> str:
    # !setplatform <session_id> <platform>
    parts = message.content[13:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setplatform <session_id> <platform>`"
    
    session_id = parts[0]
    platform = parts[1].lower()

    if platform not in consts.VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(consts.VALID_PLATFORMS)}`"

    if "-" in session_id:
        # batch mode
        try:
            a = int(session_id.split("-")[0])
            b = int(session_id.split("-")[1])
        except ValueError:
            return "Invalid session ID range. Please provide valid integers in the format `start-end`."
        if a > b or a == b:
            return "Invalid range"
        while a <= b:
            operations.set_platform_for_session(
                user,
                sessionId=a,
                platform=platform
            )
            a += 1
        return f"OK! Platform has been set to **{platform}** for sessions {session_id}"
    
    try:
        session_id = int(session_id)
    except ValueError:
        return "Invalid session ID. Please provide a valid integer."

    return operations.set_platform_for_session(user, sessionId=session_id, platform=platform)

def dm_set_date(user: storage.User, message: discord.Message) -> str:
    # !setdate <session_id> <new_date>
    parts = message.content[9:].split()
    if len(parts) != 2:
        return "Invalid command format"
    
    if not parts[1].upper().endswith("Z"):
        return "Invalid date format. Please provide the date in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)"
    
    session_id = int(parts[0])
    
    new_date = utils.datetimeFromISO8601(parts[1])
    if new_date is None:
        return "Date format is invalid"
    
    return operations.modify_session_date(
            user,
            sessionId=session_id,
            new_date=new_date
        )

def dm_last_sessions(user: storage.User, message: discord.Message) -> str:
    # !last
    # !last n
    splitted = message.content.split()
    amount = 1
    if len(splitted) == 2:
        amount = min(int(splitted[1]), 10)
    try:
        sessions = storage.Activity.select().where(storage.Activity.user == user).order_by(storage.Activity.timestamp.desc()).limit(amount)
        lines = []
        for session in sessions:
            lines.append(f"#{session.id}\t{session.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{session.game.name} ({session.platform})\t{utils.secsToHHMMSS(session.seconds)}")
        out = "```\n"
        out += "\n".join(reversed(lines))
        out += "```"
        return out
    except Exception as e:
        return f"ERROR: {e}"
    
def dm_set_game(user: storage.User, message: discord.Message) -> str:
    # !setgame <session_id> "Game Name"
    # !setgame <session_id1-session_id2> "Game Name"
    parts = message.content[9:].split('"')
    if len(parts) < 3:
        return "Invalid command format. Use: `!setgame <session_id> \"Game Name\"` or `!setgame <session_id1-session_id2> \"Game Name\"`"
    game_name = parts[1].strip()[:-1]  # Remove trailing quote
    game = operations.get_or_create_game(gameName=game_name)
    if not game:
        return f"Game '{game_name}' not found or could not be created."
    session_ids = parts[0].strip()
    parsed = utils.parseRange(session_ids)
    if parsed:
        a,b = parsed
    else:
        try:
            a = int(session_ids)
            b = a
        except ValueError:
            return "Invalid session ID. Please provide a valid integer or a range in the format `start-end`."
    while a <= b:
        activity = storage.Activity.get_or_none(storage.Activity.id == a)
        if activity is None:
            return f"Session {a} not found."
        if activity.user != user:
            return f"Session {a} does not belong to you."
        if activity.game == game:
            return f"Session {a} is already set to game {game.name}."
        operations.set_game_for_activity(activity, game)
        a += 1
    return f"Game has been set to **{game.name}** for session(s) {session_ids}."

def game_info(gameNameOrId: str) -> str:
    # !game <game_id|game_name>
    try:
        gameId = int(gameNameOrId)
        game = storage.Game.get_or_none(storage.Game.id == gameId)
    except ValueError:
        gameNameOrId = gameNameOrId.replace('"', '')
        game = storage.Game.get_or_none(storage.Game.name == gameNameOrId)

    if game is None:
        return f"Game with ID or name '{gameNameOrId}' not found."

    out = f"# {game.name}\n"
    out += f"ID: `{game.id}`\n"
    out += f"Small Image: {game.small_image}\n"
    out += f"Large Image: {game.large_image}\n"
    out += f"Steam ID: `{game.steam_id}`\n"
    out += f"SGDB ID: `{game.sgdb_id}`\n"
    
    return out

def adm_set_game_image(message: discord.Message) -> str:
    # !setgameimage <game:id> <image_url>
    # same url for both for now
    parts = message.content[14:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setgameimage <game_id> <image_url>`"
    game = storage.Game.get_or_none(storage.Game.id == int(parts[0]))
    if game is None:
        return f"ERROR: Game with ID {parts[0]} not found."
    image_url = parts[1]
    if not image_url.startswith("http"):
        return "ERROR: Image URL should start with http or https."
    operations.update_game_images(gameName=game.name, assets={
        "small_image_url": image_url,
        "large_image_url": image_url
    })
    return "OK, updated game images for game **{}**".format(game.name, game.id)

def adm_remove_game_images(message: discord.Message) -> str:
    # !removegameimages <game:id>
    id = message.content.removeprefix("!removegameimages ").strip()
    id = int(id)
    game = storage.Game.get_or_none(storage.Game.id == id)
    if game is None:
        return f"ERROR: Game with ID {id} not found."
    return operations.remove_game_images(game)

def adm_set_steam_id(message: discord.Message) -> str:
    # !setsteamid <game:id> <steam_id>
    parts = message.content[12:].strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setsteamid <game_id> <steam_id>`"
    
    game_id = int(parts[0])
    steam_id = int(parts[1])

    game = storage.Game.get_or_none(storage.Game.id == game_id)
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    
    storage.Game.update(steam_id=steam_id).where(storage.Game.id == game.id).execute()
    return f"OK! Set Steam ID {steam_id} for game {game.name}"

def adm_set_sgdb_id(message: discord.Message) -> str:
    # !setsgdbid <game:id> <sgdb_id>
    parts = message.content.removeprefix("!setsgdbid ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format"
    game_id = int(parts[0])
    sgdb_id = int(parts[1])
    game = storage.Game.get_or_none(storage.Game.id == game_id)
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    storage.Game.update(sgdb_id=sgdb_id).where(storage.Game.id == game.id).execute()
    return f"OK! **{game.name}** SGDB ID = **{sgdb_id}**"


def dm_receive(message: discord.Message) -> str:
    msg = message.content.strip()
    # Replace Apple's stupid quotes
    msg = msg.replace("“", '"').replace("”", '"')

    user = user_from_message(message)
    if user is None:
        logger.error("Could not get Oblivionis User for message: %s", message)
        return "ERROR: Try again later"

    isAdmin = str(message.author.id) in ADMINS
    if isAdmin:
        if msg.startswith("!setgameimage"):
            return adm_set_game_image(message)
        elif msg.startswith("!removegameimages"):
            return adm_remove_game_images(message)
        elif msg.startswith("!setsteamid"):
            return adm_set_steam_id(message)
        elif msg.startswith("!setsgdbid"):
            return adm_set_sgdb_id(message)

        
    if msg.startswith("!help"):
        return dm_help(isAdmin)
    elif msg.startswith("!game"):
        return game_info(msg.removeprefix('!game ').strip())
    elif msg.startswith("!add"):
        return dm_add_session(user, msg)
    elif msg.startswith("!start"):
        return dm_start_session(user, message)
    elif msg.startswith("!stop"):
        return dm_stop_session(user, message)
    elif msg.startswith("!merge"):
        return dm_merge_game(user, message)
    elif msg.startswith("!remove"):
        return dm_remove_session(user, message)
    elif msg.startswith("!platform"):
        return dm_platform(user, message)
    elif msg.startswith("!listplatforms"):
        return f"Valid platforms are:\n\n`{', '.join(consts.VALID_PLATFORMS)}`"
    elif msg.startswith("!setplatform"):
        return dm_set_platform(user, message)
    elif msg.startswith("!setdate"):
        return dm_set_date(user, message)
    elif msg.startswith("!setgame"):
        return dm_set_game(user, message)
    elif msg.startswith("!last"):
        return dm_last_sessions(user, message)
    else:
        return "Unknown command. Use `!help` to see available commands."
