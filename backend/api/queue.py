from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Depends, Request

from backend.app import app
from backend.models.map import HTTPMap, HTTPMapInDB
from backend.tasks.map import map_update
from backend.api.base import BaseAppAuth
from backend.api.user import set_response_headers, admin_role_authentificated


router = InferringRouter()
TAG_CLASS = "QueueApp"


@cbv(router)
class QueueApp(BaseAppAuth):
    @router.get("/api/queue/{name}", tags=[TAG_CLASS])
    async def get_queue(self, name: str, req: Request):
        pass

    @router.post("/api/queue/{name}", tags=[TAG_CLASS])
    async def post_queue(self, name: str, req: Request):
        pass

    @router.put("/api/queue/{name}", tags=[TAG_CLASS])
    async def put_queue(self, name: str, req: Request):
        pass

    @router.patch("/api/queue/{name}", tags=[TAG_CLASS])
    async def patch_queue(self, name: str, req: Request):
        pass

    @router.delete("/api/queue/{name}", tags=[TAG_CLASS])
    async def delete_queue(self, name: str, req: Request):
        pass


app.include_router(router)
