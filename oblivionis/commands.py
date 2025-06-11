import logging
import os
import re

import discord
from oblivionis import operations, utils, storage, consts
from typing import TypedDict, Dict
import datetime

logger = logging.getLogger("commands")

def dm_help() -> str:
    return """
# Help:
- `!help` - Show this message

# Manual addition:
- `!add "Game Name" <duration> [datetime]` - Add a session of specified duration
    - Duration can be one of these formats:
        - `123` (eg `!add "Game Name" 3600`)
        - `HH:MM:SS` (eg `!add "Game Name" 01:00:00`)
        - `XXhYYmZZs` (eg `!add "Game Name" 1h30m15s`)
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
- `!setdate <session_id> <datetime>` - Modify the date of a session. Date should be in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)
- `!setplatform <session_id> <platform>` - Set the platform for a specific session
- `!setplatform <session_id1-session_id2> <platform>` - Set the platform for a range of sessions (e.g. `!setplatform 123-456 steam-deck`)

# Platform:
- `!platform` - Show your current default platform
- `!platform <name>` - Set your default platform
    - This is the platform used when platform cannot be automatically determined (e.g. manual sessions)
- `!listplatforms` - List all valid platforms
"""

class ManualSession(TypedDict):
    gameName: str
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
    matches = [m[1] for m in re.findall(r'(["\'])(.*?)\1', message)]
    gameName = matches[0] if matches else None
    if not gameName:
        return 'ERROR: Could not extract game name'

    parts = message.split(" ")

    timestamp = None
    duration = None
    last = parts.pop() # This is the timestamp if provided
    if last.upper().endswith("Z"):
        timestamp = utils.datetimeFromISO8601(last)
        duration = utils.secsFromString(parts.pop())
    else:
        duration = utils.secsFromString(last)
    
    if duration < 0:
        return "Duration is invalid"
        
    result = operations.add_session(
                    user=user,
                    gameName=gameName,
                    seconds=duration, timestamp=timestamp)
    
    return "OK"

def dm_start_session(user: storage.User, message: discord.Message) -> str:
    # !start "Game Name"
    gameName = message.content[7:].strip('"')
    userId = str(user.id)

    if len(gameName) == 0:
        return "Missing game name"
    
    if userId in MANUAL_SESSIONS:
        return 'You already have a manual session running. Please `!stop` before starting a new one.'
    
    MANUAL_SESSIONS[userId] = {
        "gameName": gameName,
        "startTime": utils.now()
    }
    return f"You have started playing **{gameName}**. Send me `!stop` to end the session."

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
                gameName=gameName,
                seconds=seconds)
    
    if result[1]:
        if isinstance(result[1], ValueError):
            # Too short
            return f"⚠️ Session ended, but not saved.\nSessions must be atleast {consts.MINIMUM_SESSION_LENGTH} seconds (was {seconds} seconds)."
        # internal failure
        MANUAL_SESSIONS[userId] = session
        return f"ERROR: Could not save session. Your session will keep running. Please try again."
    return f"Session {result[0]} saved. You played **{gameName}** for {utils.secsToHHMMSS(seconds)} seconds!"

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

def dm_receive(message: discord.Message) -> str:
    msg = message.content.strip()
    discordUserName = message.author.name 
    user = user_from_message(message)
    if user is None:
        logger.error("Could not get Oblivionis User for message: %s", message)
        return "ERROR: Try again later"
        
    if msg.startswith("!help"):
        return dm_help()
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
    elif msg.startswith("!last"):
        return dm_last_sessions(user, message)
    else:
        return "Unknown command. Use `!help` to see available commands."
    
# IDEAS:
# !reduce <session_id> <seconds> - Reduce the session time by a certain number of seconds
# !add <session_id> <seconds> - Add a session with a specific game name and seconds