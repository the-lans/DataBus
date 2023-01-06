from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Request

from backend.app import app
from backend.models.request_message import RequestMessage
from backend.api.base import BaseAppAuth
from backend.library.redis import get_aclient
from backend.config import REDIS_QUEUE


router = InferringRouter()
TAG_CLASS = "QueueApp"


@cbv(router)
class QueueApp(BaseAppAuth):
    async def request_queue(self, name: str, req: Request) -> dict:
        conn = await get_aclient()
        message = await RequestMessage().get_from_request(req)
        message.set_proxy_url(name)
        pipeline = conn.pipeline(transaction=True)
        pipeline.multi()
        await message.create_verdicts(self.current_user)
        await pipeline.rpush(name, message.dumps())
        await pipeline.sadd(REDIS_QUEUE, name)
        await pipeline.execute()
        return await self.prepare(True)

    @router.get("/api/queue/{name}", tags=[TAG_CLASS])
    async def get_queue(self, name: str, req: Request):
        return await self.request_queue(name, req)

    @router.post("/api/queue/{name}", tags=[TAG_CLASS])
    async def post_queue(self, name: str, req: Request):
        return await self.request_queue(name, req)

    @router.put("/api/queue/{name}", tags=[TAG_CLASS])
    async def put_queue(self, name: str, req: Request):
        return await self.request_queue(name, req)

    @router.patch("/api/queue/{name}", tags=[TAG_CLASS])
    async def patch_queue(self, name: str, req: Request):
        return await self.request_queue(name, req)

    @router.delete("/api/queue/{name}", tags=[TAG_CLASS])
    async def delete_queue(self, name: str, req: Request):
        return await self.request_queue(name, req)


app.include_router(router)
