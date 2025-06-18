import logging
import discord
from oblivionis import admin_commands, operations, utils, consts
from oblivionis.storage.storage_v2 import User, Game, Platform, Activity
from typing import TypedDict, Dict
import datetime

from oblivionis.globals import ADMINS
from oblivionis.models import ManualSession

logger = logging.getLogger("commands")

def dm_help(isAdmin: bool) -> str:
    base = """
# Help:
- `!help` - Show this message

# Manual addition:
- `!add "Game Name"|alias <duration> [datetime]` - Add a session of specified duration
    - If datetime is not provided, current time is used
        - If datetime is provided, it should be in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)

# Manual start/stop:
- `!start "Game Name"|alias` - Start a manual session
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
- `!setgameimage <game_id> <url|null>`
- `!setsteamid <game_id> <steam_id|null>`
- `!setsgdbid <game_id> <sgdb_id|null>`
- `!addalias <game_id> <alias>`
- `!delalias <game_id> <alias>`
- `!setgamereleaseyear <game_id> <year>`
"""
    if isAdmin:
        return base + admin
    return base



MANUAL_SESSIONS: dict[str, ManualSession] = {}

def user_from_message(message: discord.Message) -> User | None:
    if message.author is None:
        return None
    user, created = User.get_or_create(id=message.author.id, name=message.author.name)
    if created:
        logger.info("Added new user %s %s to database", message.author.id, message.author.name)
    return user

def user_name_from_message(message: discord.Message) -> str:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.name

def dm_add_session(user: User, message: str) -> str:
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
    
    game = Game.get_or_create(name=gameName)
    
    result = operations.add_session(
                    user=user,
                    game=game,
                    seconds=duration, 
                    timestamp=timestamp)
    sesh = result[0]
    if sesh:
        return f"Session #{sesh} saved"
    return f"ERROR: {result[1]}"

def dm_start_session(user: User, msg: str) -> str:
    # !start "Game Name"
    # !start "Game Name" <platform>
    userId = str(user.id)
    if userId in MANUAL_SESSIONS:
        return 'You already have a manual session running. Please `!stop` before starting a new one.'

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
    return f"Started playing **{gameName}** on **{platform}**.\nSend `!stop` to end the session."

def dm_stop_session(user: User, message: discord.Message) -> str:
    # !stop
    userId = str(user.id)
    if userId not in MANUAL_SESSIONS:
        return "You don't have a manual session running"
    
    session = MANUAL_SESSIONS.pop(userId)
    gameName = session["gameName"]
    startTime = session["startTime"]
    duration = utils.now() - startTime
    seconds = int(duration.total_seconds())

    game, created = Game.get_or_create(name=gameName)
    platform, created = Platform.get_or_create(abbreviation=session["platform"])

    result = operations.add_session(
                user=user,
                platform=platform,
                game=game,
                seconds=seconds)
    
    sesh = result[0]
    if sesh:
        return f"Session #{sesh} saved.\nYou played **{ game }** on **{platform}** for {utils.secsToHHMMSS(int(str(sesh.seconds)))}"
    
    if isinstance(result[1], ValueError):
        return "Session ended, but not saved because it was too short"
    # internal failure
    MANUAL_SESSIONS[userId] = session
    return f"ERROR: Could not save session. Your session will keep running. Please try again."
    

def dm_merge_game(user: User, message: discord.Message) -> str:
    # !merge 123 456 
    parts = message.content.removeprefix('!merge ').strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!merge game_id1 game_id2`"
    game_id1 = int(parts[0])
    game_id2 = int(parts[1])
    return operations.merge_games(user, gameId1=game_id1, gameId2=game_id2)

def dm_remove_session(user: User, message: discord.Message) -> str:
    # !remove session_id
    msg = message.content.removeprefix('!remove ').strip()
    if not msg.isdigit():
        return "Invalid command format (not a number?)"
    msg = int(msg)
    return operations.remove_session(user, sessionId=msg)

def dm_platform(user: User, message: discord.Message) -> str:
    if message.content == "!platform":
        return f"Your default platform is **{user.default_platform}**. Use `!platform <name>` to change it."
    
    platform = message.content.removeprefix('!platform ').strip().lower()
    if platform not in consts.VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(consts.VALID_PLATFORMS)}`"
    
    return operations.set_default_platform(user, platform)

def dm_set_platform(user: User, message: discord.Message) -> str:
    # !setplatform <session_id> <platform>
    parts = message.content.removeprefix('!setplatform ').strip().split()
    if len(parts) != 2:
        return "Invalid command format"
    
    session_id = parts[0]
    platform = parts[1].lower()

    if platform not in consts.VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(consts.VALID_PLATFORMS)}`"

    parsed = utils.parseRange(session_id)
    if parsed:
        a,b = parsed
    else:
        try:
            a = int(session_id)
            b = a
        except ValueError:
            return "Invalid session ID. Please provide a valid integer or a range in the format `start-end`."
    while a <= b:
        operations.set_platform_for_session(
            user,
            sessionId=a,
            platform=platform
        )
        a += 1
    return f"OK! Platform has been set to **{platform}** for sessions {session_id}"


def dm_set_date(user: User, message: discord.Message) -> str:
    # !setdate <session_id> <new_date>
    parts = message.content.removeprefix('!setdate ').strip().split()
    if len(parts) != 2:
        return "Invalid format"
    
    session_id = int(parts[0])
    new_date = utils.datetimeFromISO8601(parts[1])
    if new_date is None:
        return "Date format is invalid"
    
    return operations.modify_session_date(
            user,
            sessionId=session_id,
            new_date=new_date
        )

def dm_last_sessions(user: User, message: discord.Message) -> str:
    # !last
    # !last n
    splitted = message.content.split()
    amount = 1
    if len(splitted) == 2:
        amount = min(int(splitted[1]), 10)
    sessions = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).limit(amount)
    lines = []
    for session in sessions:
        lines.append(f"#{session}\t{session.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{session.game.name} ({session.platform.abbreviation})\t{utils.secsToHHMMSS(session.seconds)}")
    out = "```\n"
    out += "\n".join(reversed(lines))
    out += "```"
    return out
    
def dm_set_game(user: User, message: discord.Message) -> str:
    # !setgame <session_id> "Game Name"
    # !setgame <session_id1-session_id2> "Game Name"

    msg = message.content.replace('"', '')
    msg = msg.removeprefix('!setgame ').strip().split()
    
    session_ids = msg.pop(0).strip()
    game_name = " ".join(msg).strip()
    game = operations.get_or_create_game(gameName=game_name)
    if not game:
        return f"Game '{game_name}' not found or could not be created."
    
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
        activity = Activity.get_or_none(Activity == a)
        if activity is None:
            return f"Session {a} not found."
        if activity.user != user:
            return f"Session {a} does not belong to you."
        if activity.game == game:
            return f"Session {a} is already set to game {game.name}."
        operations.set_game_for_activity(activity, game)
        a += 1
    return f"Game has been set to **{game.name}** for session(s) {session_ids}."

def dm_game_info(message: discord.Message) -> str:
    # !game <game_id|game_name>
    msg = message.content.removeprefix('!game ').strip()
    try:
        gameId = int(msg)
        game = Game.get_or_none(Game == gameId)
    except ValueError:
        msg = msg.replace('"', '')
        game = Game.get_or_none(Game.name == msg)

    if game is None:
        return f"Game with ID or name '{msg}' not found."

    out = f"# {game.name}\n"
    out += f"ID: `{game.id}`\n"
    out += f"Release Year: `{game.release_year}`\n"
    out += f"Steam ID: `{game.steam_id}`\n"
    out += f"SGDB ID: `{game.sgdb_id}`\n"
    out += f"Image URL: {game.image_url}\n"
    out += f"Aliases: `{', '.join(game.aliases)}`\n"
    
    return out



def try_expand_alias(msg: str) -> str:
    # if quotes: it should be a full title 
    if '"' in msg:
        return msg
    # if no quotes: maybe an alias?
    splitted = msg.split()
    alias = splitted[1].strip()
    game = operations.get_game_by_alias(alias)
    if game is None:
        return msg # did not find alias: return original
    # Replace alias with full game name (hax...)
    splitted[1] = f'"{game.name}"'
    msg = " ".join(splitted)
    return msg

def dm_receive(message: discord.Message) -> str:
    msg = utils.normalizeQuotes(message.content.strip())

    user = user_from_message(message)
    if user is None:
        logger.error("Could not get Oblivionis User for message: %s", message)
        return "ERROR: Try again later"

    isAdmin = str(message.author.id) in ADMINS
    if isAdmin:
        if msg.startswith("!setgameimage"):
            return admin_commands.adm_set_game_image(message)
        elif msg.startswith("!setsteamid"):
            return admin_commands.adm_set_steam_id(message)
        elif msg.startswith("!setsgdbid"):
            return admin_commands.adm_set_sgdb_id(message)
        elif msg.startswith("!addalias"):
            return admin_commands.adm_add_alias(message)
        elif msg.startswith("!delalias"):
            return admin_commands.adm_del_alias(message)
        elif msg.startswith("!setgamereleaseyear"):
            return admin_commands.adm_set_game_release_year(message)

    if msg.startswith("!help"):
        return dm_help(isAdmin)
    elif msg.startswith("!game"):
        return dm_game_info(message=message)
    elif msg.startswith("!add"):
        msg = try_expand_alias(msg)
        return dm_add_session(user, msg)
    elif msg.startswith("!start"):
        msg = try_expand_alias(msg)
        return dm_start_session(user, msg)
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
