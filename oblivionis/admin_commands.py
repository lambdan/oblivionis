import datetime
import discord

from oblivionis import operations
from oblivionis.storage.storage_v2 import Game, Platform, User


def adm_set_game_image(message: discord.Message) -> str:
    # !setgameimage <game_id> <image_url|null>
    # same url for both for now
    parts = message.content.removeprefix("!setgameimage ").strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setgameimage <game_id> <image_url>`"
    game = Game.get_or_none(Game.id == int(parts[0])) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {parts[0]} not found."
    image_url = parts[1]
    if image_url != "null" and not image_url.startswith("http"):
        return "ERROR: Image URL should start with http or https, or be null"
    game.image_url = None if image_url == "null" else image_url
    game.save()
    return f"OK, updated game image for game **{game.name}**"



def adm_set_steam_id(message: discord.Message) -> str:
    # !setsteamid <game:id> <steam_id>
    parts = message.content.removeprefix("!setsteamid ").strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setsteamid <game_id> <steam_id>`"
    game_id = int(parts[0])
    steam_id = None if parts[1] == "null" else int(parts[1])
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    Game.update(steam_id=steam_id).where(Game.id == game.id).execute() # type: ignore
    return f"OK! Set Steam ID {steam_id} for game {game.name}"

def adm_set_sgdb_id(message: discord.Message) -> str:
    # !setsgdbid <game:id> <sgdb_id>
    parts = message.content.removeprefix("!setsgdbid ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format"
    game_id = int(parts[0])
    sgdb_id = None if parts[1] == "null" else int(parts[1])
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    Game.update(sgdb_id=sgdb_id).where(Game.id == game.id).execute() # type: ignore
    return f"OK! **{game.name}** SGDB ID = **{sgdb_id}**"

def adm_add_alias(message: discord.Message) -> str:
    # !addalias <game_id> <alias>
    parts = message.content.removeprefix("!addalias ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format. Use: `!addalias <game_id> <alias>`"
    game_id = int(parts.pop(0))
    alias = " ".join(parts).strip()

    # check if any game already uses this alias
    aliasedGame = operations.get_game_by_alias(alias)
    if aliasedGame:
        return f"ERROR: Alias '{alias}' already exists for game {aliasedGame.name} (ID {aliasedGame})."
    
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    if game.aliases and alias in game.aliases:
        return f"Alias '{alias}' already exists for game {game.name}."
    if not game.aliases:
        game.aliases = []
    game.aliases.append(alias)
    game.save()
    return f"OK! Added alias '{alias}' for game {game.name}"

def adm_del_alias(message: discord.Message) -> str:
    # !delalias <game_id> <alias>
    parts = message.content.removeprefix("!delalias ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format. Use: `!delalias <game_id> <alias>`"
    game_id = int(parts.pop(0))
    alias = " ".join(parts).strip()
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    if not game.aliases or alias not in game.aliases:
        return f"Alias '{alias}' does not exist for game {game.name}."
    game.aliases.remove(alias)
    game.save()
    return f"OK! Removed alias '{alias}' from game {game.name}"

def adm_set_game_release_year(message: discord.Message) -> str:
    # !setgamereleaseyear <game_id> <year>
    parts = message.content.removeprefix("!setgamereleaseyear ").strip().split()
    if len(parts) != 2:
        return "ERROR: Invalid command format. Use: `!setgamereleaseyear <game_id> <year>`"
    game_id = int(parts[0])
    year = int(parts[1])

    year_now = datetime.datetime.now(datetime.UTC).year
    if year < 1950 or year > year_now:
        return f"ERROR: Invalid year {year}. It should be between 1950 and {year_now}."
    
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    
    game.release_year = year
    game.save()
    return f"OK! Set release year {year} for game {game.name}"

def adm_add_platform(message: discord.Message) -> str:
    # !addplatform <platform_abbreviation> <platform_name>
    parts = message.content.removeprefix("!addplatform ").strip().split()

    abbr = parts.pop(0)
    name = " ".join(parts).strip()

    reply = []
    platform, created = Platform.get_or_create(abbreviation=abbr)
    if created:
        reply.append("Added new platform")
    platform.name = name if len(name) > 0 else None
    platform.save()
    reply.append(f"Abbreviation: **{abbr}**, Name: **{name}**")
    return "\n".join(reply)

def adm_del_platform(message: discord.Message) -> str:
    # !delplatform <platform_abbreviation>
    parts = message.content.removeprefix("!delplatform ").strip().split()
    abbr = parts[0].strip()

    platform = Platform.get_or_none(Platform.abbreviation == abbr)
    if platform is None:
        return "Platform not found"
    
    platform.delete_instance()
    return "OK, deleted platform " + abbr

def adm_delete_activity(message: discord.Message) -> str:
    # !adm_deleteactivity <activity_id>
    i = int(message.content.split()[1].strip())
    activity = Activity.get_or_none(Activity.id == i) # type: ignore
    if activity is None:
        return f"ERROR: Activity with ID {i} not found."
    activity.delete_instance()
    return f"OK! Deleted activity {i}"

def adm_toggle_block_commands(message: discord.Message) -> str:
    # !adm_toggleblockcommands <user_id>
    i = int(message.content.split()[1].strip())
    user = User.get_or_none(User.id == i)
    if user is None:
        return f"ERROR: User with ID {i} not found."
    user.bot_commands_blocked = not user.bot_commands_blocked
    user.save()
    status = "blocked 🛑" if user.bot_commands_blocked else "unblocked ✅"
    return f"OK! User {user.name} (ID {user.id}) is now {status} from using bot commands."