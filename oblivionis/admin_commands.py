import datetime
import discord

from oblivionis import operations, storage


def adm_set_game_image(message: discord.Message) -> str:
    # !setgameimage <game_id> <image_url|null>
    # same url for both for now
    parts = message.content.removeprefix("!setgameimage ").strip().split()
    if len(parts) != 2:
        return "Invalid command format. Use: `!setgameimage <game_id> <image_url>`"
    game = storage.Game.get_or_none(storage.Game.id == int(parts[0]))
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
    sgdb_id = None if parts[1] == "null" else int(parts[1])
    game = storage.Game.get_or_none(storage.Game.id == game_id)
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    storage.Game.update(sgdb_id=sgdb_id).where(storage.Game.id == game.id).execute()
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
        return f"ERROR: Alias '{alias}' already exists for game {aliasedGame.name} (ID {aliasedGame.id})."
    
    game = storage.Game.get_or_none(storage.Game.id == game_id)
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
    game = storage.Game.get_or_none(storage.Game.id == game_id)
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
    
    game = storage.Game.get_or_none(storage.Game.id == game_id)
    if game is None:
        return f"ERROR: Game with ID {game_id} not found."
    
    game.release_year = year
    game.save()
    return f"OK! Set release year {year} for game {game.name}"

