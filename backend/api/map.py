from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Depends, Response

from backend.app import app
from backend.models.map import HTTPMap, HTTPMapInDB
from backend.tasks.map import map_update
from backend.api.base import BaseAppAuth
from backend.api.user import set_response_headers, admin_role_authentificated


router = InferringRouter()
TAG_CLASS = "HTTPMapApp"


@cbv(router)
class HTTPMapApp(BaseAppAuth):
    @classmethod
    async def get_object_id(cls, item_id):
        return await cls.get_one_object(HTTPMapInDB.select().where(HTTPMapInDB.id == item_id))

    @router.get("/api/map/list", tags=[TAG_CLASS])
    async def get_items(self):
        return await self.get_list(HTTPMapInDB)

    @router.get("/api/map/update", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_maps(self):
        return {"success": True, "items": await map_update()}

    @router.get("/api/map/{item_id}", tags=[TAG_CLASS])
    async def get_item(self, item_id: int):
        item_db = await self.get_object_id(item_id)
        res = await self.prepare(item_db)
        if item_db is not None:
            res.update(await item_db.dict)
        return res

    @router.post("/api/map/new", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def new_item(self, item: HTTPMap = Depends()):
        return await HTTPMapInDB.update_or_create(item, ret={"success": True})

    @router.put("/api/map/{item_id}", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_item(self, item_id: int, item: HTTPMap = Depends()):
        item_db = await self.get_object_id(item_id)
        res = await self.prepare(item_db)
        if item_db is not None:
            return await HTTPMapInDB.update_or_create(item, item_db, ret=res)
        return res


app.include_router(router)


@app.options("/api/map/list", tags=[TAG_CLASS])
async def options_object_id(response: Response):
    return await set_response_headers(response)


@app.options("/api/map/{item_id}", tags=[TAG_CLASS])
async def options_item(response: Response):
    return await set_response_headers(response)


@app.options("/api/map/new", tags=[TAG_CLASS])
async def options_new_item(response: Response):
    return await set_response_headers(response)
