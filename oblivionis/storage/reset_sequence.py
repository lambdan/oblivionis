import logging
from peewee import fn
logger = logging.getLogger("reset_sequence")

def reset_sequence(model):
    table = model._meta.table_name
    pk_field = model._meta.primary_key
    sequence_name = f"{table}_{pk_field.name}_seq"
    max_id = model.select(fn.MAX(pk_field)).scalar() or 0
    new_max_id = int(max_id) + 1
    model._meta.database.execute_sql(
        f"SELECT setval('{sequence_name}', {new_max_id}, false);"
    )
    logger.info(f"Reset sequence for {table} to {new_max_id}.")

def reset_sequences(list_of_models):
    for model in list_of_models:
        reset_sequence(model)
    logger.info("Sequences reset successfully")