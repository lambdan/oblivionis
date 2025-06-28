import uvicorn
import asyncio
import os
from oblivionis.bot import bot
from oblivionis.storage import migrate_v1_to_v2, storage_v1, storage_v2
from oblivionis.api import app

async def start_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def start_bot():  
    await bot.start(os.environ["DISCORD_TOKEN"])

async def async_main():
    await asyncio.gather(
        start_api(),
        start_bot(),
    )

def main():
    #storage_v1.connect_db()
    storage_v2.connect_db()
    #migrate_v1_to_v2.migrate()
    #storage_v1.disconnect_db()
    asyncio.run(async_main())

if __name__ == "__main__":
    main()