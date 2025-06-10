from oblivionis import operations, utils
from oblivionis.consts import VALID_PLATFORMS
from oblivionis.storage import User
import datetime

def dm_help() -> str:
    return """
# Help:
- `!help` - Show this message

# Retroactive entry:
- `!add "Game Name" n` - Add a session of n seconds (timestamp will be now)

# Manual start/stop:
- `!start "Game Name"` - Start a manual session
- `!stop` - Stop the current manually started session

# Maintenance:
- `!merge <game_id1> <game_id2>` - Merge game_id1 into game_id2
- `!remove <session_id>` - Remove session with id
- `!setdate <session_id> <new_date>` - Modify the date of a session. Date should be in ISO8601 UTC format (e.g. `2023-10-01T12:00:00Z`)
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
    # !add "Game Name" seconds
    parts = message.content[5:].rsplit(" ", 1)
    if len(parts) != 2:
        return 'Invalid command. Use: `!add "Game Name" seconds`'
    
    gameName = parts[0].strip('"')
    try:
        seconds = int(parts[1])
    except ValueError:
        return "Invalid seconds value. Please provide a valid integer."
    
    return operations.add_session(userId=user_id_from_message(message),
                userName=user_name_from_message(message),
                gameName=gameName,
                seconds=seconds)

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
        "startTime": datetime.datetime.now(datetime.UTC),
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
    duration = datetime.datetime.now(datetime.UTC) - startTime
    seconds = int(duration.total_seconds())
    operations.add_session(userId=userId,
                userName=user_name_from_message(message),
                gameName=gameName,
                seconds=seconds)
    return f"You played **{gameName}** for {seconds} seconds!"

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
    else:
        return "Unknown command. Use `!help` to see available commands."
    
# IDEAS:
# !reduce <session_id> <seconds> - Reduce the session time by a certain number of seconds
# !add <session_id> <seconds> - Add a session with a specific game name and seconds
# !last - Show the last session