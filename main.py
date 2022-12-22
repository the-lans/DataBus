import uvicorn
import asyncio
from backend.config import DB_SETTINGS
from backend.api import *
from backend.tasks.map import map_update


if __name__ == "__main__":
    print("Init...")
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(map_update())
    ioloop.close()

    print("Run...")
    uvicorn.run(app, host=DB_SETTINGS['DOMAIN'], port=DB_SETTINGS['PORT'])
