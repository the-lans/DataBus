import uvicorn
import asyncio
from multiprocessing import Process

from backend.config import DB_SETTINGS
from backend.api import *
from backend.tasks.map import HTTPMapData
from backend.tasks.common_headers import HTTPHeadersData
from backend.tasks.base import processing
from backend.tasks.processing import Processing
from backend.library.logger import MainLogger


if __name__ == "__main__":
    print("Init...")
    MainLogger.update_main_logger()
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(HTTPMapData.update())
    ioloop.run_until_complete(HTTPHeadersData.update())
    ioloop.close()

    proc = Processing(timeout=0.1)
    proc_requests = Process(target=processing, args=(proc,))

    print("Run...")
    proc_requests.start()
    uvicorn.run(app, host=DB_SETTINGS['DOMAIN'], port=DB_SETTINGS['PORT'])
    proc.stop_polling()
    proc_requests.join()
