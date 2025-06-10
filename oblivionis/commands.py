import re
from oblivionis import operations, utils
from oblivionis.consts import VALID_PLATFORMS
from oblivionis.storage import User, Activity
import datetime

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

MANUAL_SESSIONS = {}

def user_id_from_message(message) -> int:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.id

def user_name_from_message(message) -> str:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.name

def dm_add_session(message) -> str:
    # !add "Game Name" <duration> [timestamp]
    matches = [m[1] for m in re.findall(r'(["\'])(.*?)\1', message.content)]
    gameName = matches[0] if matches else None
    if not gameName:
        return 'ERROR: Could not extract game name'

    parts = message.content.split(" ")

    try:
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
    
        return operations.add_session(userId=user_id_from_message(message),
                    userName=user_name_from_message(message),
                    gameName=gameName,
                    seconds=duration, timestamp=timestamp)
    except:
        return "Something went wrong. Double check your command format"

def dm_start_session(message) -> str:
    # !start "Game Name"
    userId = user_id_from_message(message)
    gameName = message.content[7:].strip('"')
    if not gameName:
        return 'Invalid command format. Use: `!start "Game Name"`'
    if userId in MANUAL_SESSIONS:
        return 'You already have a manual session running. Please `!stop` before starting a new one.'
    MANUAL_SESSIONS[userId] = {
        "gameName": gameName,
        "startTime": utils.now()
    }
    return f"You have started playing **{gameName}**. Use `!stop` to end the session."

def dm_stop_session(message) -> str:
    # !stop
    userId = user_id_from_message(message)
    if userId not in MANUAL_SESSIONS:
        return "You don't have a manual session running"
    session = MANUAL_SESSIONS.pop(userId)
    gameName = session["gameName"]
    startTime = session["startTime"]
    duration = utils.now() - startTime
    seconds = int(duration.total_seconds())
    operations.add_session(userId=userId,
                userName=user_name_from_message(message),
                gameName=gameName,
                seconds=seconds)
    return f"You played **{gameName}** for {utils.secsToHHMMSS(seconds)} seconds!"

def dm_merge_game(message) -> str:
    # !merge 123 456 # Merge game with ID 123 into game with ID 456
    parts = message.content[7:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!merge game_id1 game_id2`"
    try:
        game_id1 = int(parts[0])
        game_id2 = int(parts[1])
    except ValueError:
        return "Invalid game IDs. Please provide valid integers."
    userId = user_id_from_message(message)
    return operations.merge_games(userId=userId, gameId1=game_id1, gameId2=game_id2)

def dm_remove_session(message) -> str:
    # !remove session_id
    parts = message.content[8:].split()
    if len(parts) != 1:
        return "Invalid command format. Use: `!remove session_id`"
    
    try:
        session_id = int(parts[0])
    except ValueError:
        return "Invalid session ID"
    
    return operations.remove_session(userId=user_id_from_message(message), sessionId=session_id)

def dm_platform(message) -> str:
    userId = user_id_from_message(message)
    if message.content == "!platform":
        user = User.get_or_none(User.id == userId)
        if user is None:
            return "User not found"
        return f"Your default platform is **{user.default_platform}**. Use `!platform <name>` to change it."
    
    parts = message.content[10:].split()
    if len(parts) != 1:
        return "Invalid command format. Use: `!platform <name>`"
    
    platform = parts[0].lower()
    if platform not in VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(VALID_PLATFORMS)}`"
    
    userId = user_id_from_message(message)
    return operations.set_default_platform(userId=userId, platform=platform)

def dm_set_platform(message) -> str:
    # !setplatform <session_id> <platform>
    parts = message.content[13:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setplatform <session_id> <platform>`"
    
    session_id = parts[0]
    platform = parts[1].lower()

    if platform not in VALID_PLATFORMS:
        return f"Invalid platform. Valid platforms are: `{', '.join(VALID_PLATFORMS)}`"

    userId = user_id_from_message(message)

    if "-" in session_id:
        # batch mode
        try:
            a = int(session_id.split("-")[0])
            b = int(session_id.split("-")[1])
        except ValueError:
            return "Invalid session ID range. Please provide valid integers in the format `start-end`."
        if a > b:
            return "Invalid range. The first number must be less than or equal to the second."
        while a <= b:
            operations.set_platform_for_session(
                userId=userId,
                sessionId=a,
                platform=platform
            )
            a += 1
        return f"OK! Platform has been set to **{platform}** for sessions {session_id}"
    
    try:
        session_id = int(session_id)
    except ValueError:
        return "Invalid session ID. Please provide a valid integer."

    return operations.set_platform_for_session(userId=userId, sessionId=session_id, platform=platform)

def dm_set_date(message) -> str:
    # !setdate <session_id> <new_date>
    parts = message.content[9:].split()
    if len(parts) != 2:
        return "Invalid command format"
    
    if not parts[1].upper().endswith("Z"):
        return "Invalid date format. Please provide the date in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)"
    
    try:
        session_id = int(parts[0])
        new_date = utils.datetimeFromISO8601(parts[1])
        return operations.modify_session_date(
            userId=user_id_from_message(message),
            sessionId=session_id,
            new_date=new_date
        )
    except Exception as e:
        return f"ERROR occurred: {e}"

def dm_last_sessions(message) -> str:
    # !last
    # !last n
    userId = user_id_from_message(message)
    splitted = message.content.split()
    amount = 1
    if len(splitted) == 2:
        amount = min(int(splitted[1]), 10)
    try:
        sessions = Activity.select().where(Activity.user == User.get(User.id == userId)).order_by(Activity.timestamp.desc()).limit(amount)
        lines = []
        for session in sessions:
            lines.append(f"#{session.id}\t{session.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{session.game.name} ({session.platform})\t{utils.secsToHHMMSS(session.seconds)}")
        out = "```\n"
        out += "\n".join(reversed(lines))
        out += "```"
        return out
    except Activity.DoesNotExist:
        return "You have no sessions recorded."
    except User.DoesNotExist:
        return "User not found."

def dm_receive(message) -> str:
    if message.content.startswith("!help"):
        return dm_help()
    elif message.content.startswith("!add"):
        return dm_add_session(message)
    elif message.content.startswith("!start"):
        return dm_start_session(message)
    elif message.content.startswith("!stop"):
        return dm_stop_session(message)
    elif message.content.startswith("!merge"):
        return dm_merge_game(message)
    elif message.content.startswith("!remove"):
        return dm_remove_session(message)
    elif message.content.startswith("!platform"):
        return dm_platform(message)
    elif message.content.startswith("!listplatforms"):
        return f"Valid platforms are:\n\n`{', '.join(VALID_PLATFORMS)}`"
    elif message.content.startswith("!setplatform"):
        return dm_set_platform(message)
    elif message.content.startswith("!setdate"):
        return dm_set_date(message)
    elif message.content.startswith("!last"):
        return dm_last_sessions(message)
    else:
        return "Unknown command. Use `!help` to see available commands."
    
# IDEAS:
# !reduce <session_id> <seconds> - Reduce the session time by a certain number of seconds
# !add <session_id> <seconds> - Add a session with a specific game name and seconds