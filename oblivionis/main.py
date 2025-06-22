import time
import uvicorn
import asyncio
import os
from oblivionis.bot import bot
from oblivionis.storage import migrate_v1_to_v2, storage_v1, storage_v2
from api import app as fastapi_app

async def start_api():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def start_bot():  
    await bot.start(os.environ["DISCORD_TOKEN"])

async def start_sync():
    while True:
        await asyncio.sleep(60) 
        storage_v2.sync_totals()
        

async def main():
    await asyncio.gather(
        start_api(),
        start_bot(),
        start_sync()
    )

if __name__ == "__main__":
    storage_v1.connect_db()
    storage_v2.connect_db()
    migrate_v1_to_v2.migrate()
    storage_v1.disconnect_db()

    asyncio.run(main())