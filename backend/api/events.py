from multiprocessing import Process

from backend.api import app
from backend.tasks.map import HTTPMapData
from backend.tasks.common_headers import HTTPHeadersData
from backend.tasks.base import processing
from backend.tasks.processing import Processing
from backend.library.logger import MainLogger


_proc = Processing(timeout=0.1)
_proc_requests = Process(target=processing, args=(_proc,))


@app.on_event("startup")
async def startup_event():
    global _proc_requests
    MainLogger.update_main_logger()
    await HTTPMapData.update()
    await HTTPHeadersData.update()
    _proc_requests.start()


@app.on_event("shutdown")
def shutdown_event():
    global _proc, _proc_requests
    if _proc:
        _proc.stop_polling()
    if _proc_requests:
        _proc_requests.join()
