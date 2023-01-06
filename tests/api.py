from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Request
from typing import Dict
import json
from time import perf_counter
import asyncio

from backend.config import ArgParse
from backend.library.logger import MainLogger
from backend.app import app
from backend.api.base import BaseAppAuth
from backend.models.request_message import RequestMessage


router = InferringRouter()
TAG_CLASS = "TestApp"
_req_item: Dict[str, int] = {'get_item': 0, 'new_item': 0, 'update_item': 0}
_req_time_start: float = perf_counter()
_req_counter = 0
_req_num = 0


@cbv(router)
class TestApp(BaseAppAuth):
    @staticmethod
    def statistic(message: RequestMessage, req_name: str, res: dict = None):
        global _req_item, _req_counter
        if ArgParse.getter('detail'):
            message.log_write(res)
        _req_item[req_name] += 1
        _req_counter += 1

    @router.get("/api/test/stat/start", tags=[TAG_CLASS])
    async def get_stat_start(self, num: int):
        global _req_time_start, _req_counter, _req_num
        _req_item.update({'get_item': 0, 'new_item': 0, 'update_item': 0})
        _req_time_start = perf_counter()
        _req_counter, _req_num = 0, num
        return {"success": True}

    @router.get("/api/test/stat/slice", tags=[TAG_CLASS])
    async def get_stat_slice(self):
        global _req_time_start, _req_counter, _req_num
        _logger_print = MainLogger.main_logger().info
        _counter = 0
        delay = 10
        while _req_counter < _req_num and _counter < delay * 50:
            _counter += 1
            await asyncio.sleep(1 / delay)
        if _counter >= delay * 50:
            MainLogger.main_logger().warning("Counter fail!")
        _logger_print(f"Statistic: {json.dumps({**_req_item, 'time_start': perf_counter() - _req_time_start})}")
        return {"success": True, **_req_item, "time_start": perf_counter() - _req_time_start}

    @router.get("/api/test/{item_id}", tags=[TAG_CLASS])
    async def get_item(self, item_id: int, req: Request):
        message = await RequestMessage().get_from_request(req)
        res = {"success": True, "item_id": item_id} if item_id else {"success": False}
        self.statistic(message, 'get_item', res)
        return res

    @router.post("/api/test/new", tags=[TAG_CLASS])
    async def new_item(self, req: Request):
        message = await RequestMessage().get_from_request(req)
        res = {"success": True}
        self.statistic(message, 'new_item', res)
        return res

    @router.put("/api/test/{item_id}", tags=[TAG_CLASS])
    async def update_item(self, item_id: int, req: Request):
        message = await RequestMessage().get_from_request(req)
        res = {"success": True, "item_id": item_id} if item_id else {"success": False}
        self.statistic(message, 'update_item', res)
        return res


app.include_router(router)
