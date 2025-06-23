from oblivionis.storage import storage_v1, storage_v2
from oblivionis.storage.reset_sequence import reset_sequences
import logging
logger = logging.getLogger("migrate_v1_to_v2")

def migrate():
    for user in storage_v1.User.select():
        if not storage_v2.User.get_or_none(storage_v2.User.id == user.id):
            storage_v2.User.create(
                id=user.id,
                name=user.name,
                default_platform=storage_v2.Platform.get_or_create(abbreviation=user.default_platform.replace("-", ""))[0]
            )
    for game in storage_v1.Game.select():
        if not storage_v2.Game.get_or_none(storage_v2.Game == game):
            storage_v2.Game.create(
                id=game.id,
                name=game.name,
                steam_id=game.steam_id,
                sgdb_id=game.sgdb_id,
                image_url=game.image_url,
                aliases=game.aliases,
                release_year=game.release_year
            )
    for activity in storage_v1.Activity.select():
        if not storage_v2.Activity.get_or_none(storage_v2.Activity == activity):
            user = storage_v2.User.get_or_create(id=activity.user.id)[0]
            game = storage_v2.Game.get_or_create(id=activity.game.id)[0]
            platform = storage_v2.Platform.get_or_create(abbreviation=activity.platform.replace("-", ""))[0]
            storage_v2.Activity.create(
                id=activity.id,
                timestamp=activity.timestamp,
                user=user,
                game=game,
                seconds=activity.seconds,
                platform=platform
            )
    storage_v1.Activity.drop_table()
    storage_v1.Game.drop_table()
    storage_v1.User.drop_table()
    reset_sequences([storage_v2.Platform, storage_v2.Game, storage_v2.Activity])
    logger.info("Migration completed successfully :D")