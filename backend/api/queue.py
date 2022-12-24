from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Request

from backend.app import app
from backend.models.request_message import RequestMessage
from backend.api.base import BaseAppAuth
from backend.library.redis import redis_call


router = InferringRouter()
TAG_CLASS = "QueueApp"


@cbv(router)
class QueueApp(BaseAppAuth):
    async def request_queue(self, name: str, req: Request):
        message = RequestMessage().get_from_request(req)
        message.set_proxy_url(name)
        await redis_call("rpush", message.dumps())
        await message.create_verdicts(self.current_user)

    @router.get("/api/queue/{name}", tags=[TAG_CLASS])
    async def get_queue(self, name: str, req: Request):
        await self.request_queue(name, req)

    @router.post("/api/queue/{name}", tags=[TAG_CLASS])
    async def post_queue(self, name: str, req: Request):
        await self.request_queue(name, req)

    @router.put("/api/queue/{name}", tags=[TAG_CLASS])
    async def put_queue(self, name: str, req: Request):
        await self.request_queue(name, req)

    @router.patch("/api/queue/{name}", tags=[TAG_CLASS])
    async def patch_queue(self, name: str, req: Request):
        await self.request_queue(name, req)

    @router.delete("/api/queue/{name}", tags=[TAG_CLASS])
    async def delete_queue(self, name: str, req: Request):
        await self.request_queue(name, req)


app.include_router(router)
