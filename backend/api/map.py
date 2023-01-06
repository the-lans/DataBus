from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Path, Depends, Response

from backend.app import app
from backend.models.map import HTTPMap, HTTPMapInDB
from backend.tasks.map import HTTPMapData
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
        return {"items": list(HTTPMapData.data_dict.values())}

    @router.get("/api/map/update", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_maps(self):
        items = await HTTPMapData.update()
        return {"success": True, "items": list(items.values())}

    @router.get("/api/map/{item_id}", tags=[TAG_CLASS])
    async def get_item(self, item_id: int = Path()):
        return (
            {"success": True, **HTTPMapData.data_dict[item_id]}
            if item_id in HTTPMapData.data_dict
            else {"success": False}
        )

    @router.post("/api/map/new", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def new_item(self, item: HTTPMap = Depends()):
        res = await HTTPMapInDB.update_or_create(item, ret={"success": True})
        await HTTPMapData.update()
        return res

    @router.put("/api/map/{item_id}", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_item(self, item_id: int = Path(), item: HTTPMap = Depends()):
        item_db = await self.get_object_id(item_id)
        res = await self.prepare(item_db)
        if item_db is not None:
            res = await HTTPMapInDB.update_or_create(item, item_db, ret=res)
            await HTTPMapData.update()
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
