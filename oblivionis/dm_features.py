from oblivionis import storage, bot
import datetime

MANUAL_SESSIONS = {}

def user_id_from_message(message) -> int:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.id

def user_name_from_message(message) -> str:
    if message.author is None:
        raise ValueError("Message author is None")
    return message.author.name


def dm_help() -> str:
    return (
        "Available commands:\n"
        "```"
        '!add "Game Name" seconds - Add a session of n seconds to the game\n'
        '!start "Game Name" - Start a manual session\n'
        "!stop - Stop the current manually started session\n"
        "!merge game_id1 game_id2 - Merge game with ID game_id1 into game with ID game_id2\n"
        "!remove session_id - Remove session with the given ID\n"
        "```"
    )

def dm_add_session(message) -> str:
    # !add "Game Name" seconds
    parts = message.content[5:].rsplit(" ", 1)
    if len(parts) != 2:
        return "Invalid command format. Use: !add \"Game Name\" seconds"
    
    gameName = parts[0].strip('"')
    try:
        seconds = int(parts[1])
    except ValueError:
        return "Invalid seconds value. Please provide a valid integer."
    
    return bot.add_session(userId=user_id_from_message(message),
                userName=user_name_from_message(message),
                gameName=gameName,
                seconds=seconds)




def dm_start_session(message) -> str:
    # !start "Game Name"
    userId = user_id_from_message(message)
    gameName = message.content[7:].strip('"')
    if not gameName:
        return 'Invalid command format. Use: !start "Game Name"'
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
    bot.add_session(userId=userId,
                userName=user_name_from_message(message),
                gameName=gameName,
                seconds=seconds)
    return f"You played **{gameName}** for {seconds} seconds!"

def dm_merge_game(message) -> str:
    # !merge 123 456 # Merge game with ID 123 into game with ID 456
    parts = message.content[7:].split()
    if len(parts) != 2:
        return "Invalid command format. Use: !merge game_id1 game_id2"
    try:
        game_id1 = int(parts[0])
        game_id2 = int(parts[1])
    except ValueError:
        return "Invalid game IDs. Please provide valid integers."
    userId = user_id_from_message(message)
    return storage.merge_games(userId=userId, gameId1=game_id1, gameId2=game_id2)

def dm_remove_session(message) -> str:
    # !remove session_id
    parts = message.content[8:].split()
    if len(parts) != 1:
        return "Invalid command format. Use: !remove session_id"
    
    try:
        session_id = int(parts[0])
    except ValueError:
        return "Invalid session ID. Please provide a valid integer."
    
    return storage.remove_session(userId=user_id_from_message(message), sessionId=session_id)

def dm_receive(message) -> str:
    if message.content.startswith("!help"):
        return dm_help()
    elif message.content.startswith("!add "):
        return dm_add_session(message)
    elif message.content.startswith("!start "):
        return dm_start_session(message)
    elif message.content.startswith("!stop"):
        return dm_stop_session(message)
    elif message.content.startswith("!merge "):
        return dm_merge_game(message)
    elif message.content.startswith("!remove "):
        return dm_remove_session(message)
    else:
        return "Unknown command. Use `!help` to see available commands."