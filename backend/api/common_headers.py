from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Path, Depends, Response

from backend.app import app
from backend.models.common_headers import CommonHeadersInDB, CommonHeaders
from backend.tasks.common_headers import HTTPHeadersData
from backend.api.base import BaseAppAuth
from backend.api.user import set_response_headers, admin_role_authentificated


router = InferringRouter()
TAG_CLASS = "CommonHeadersApp"


@cbv(router)
class CommonHeadersApp(BaseAppAuth):
    @classmethod
    async def get_object_id(cls, item_id):
        return await cls.get_one_object(CommonHeadersInDB.select().where(CommonHeadersInDB.id == item_id))

    @router.get("/api/headers/list", tags=[TAG_CLASS])
    async def get_items(self):
        return {"items": list(HTTPHeadersData.data_dict.values())}

    @router.get("/api/headers/update", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_headers(self):
        items = await HTTPHeadersData.update()
        return {"success": True, "items": list(items.values())}

    @router.get("/api/headers/{item_id}", tags=[TAG_CLASS])
    async def get_item(self, item_id: int):
        return (
            {"success": True, **HTTPHeadersData.data_dict[item_id]}
            if item_id in HTTPHeadersData.data_dict
            else {"success": False}
        )

    @router.post("/api/headers/new", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def new_item(self, item: CommonHeaders = Depends()):
        res = await CommonHeadersInDB.update_or_create(item, ret={"success": True})
        await HTTPHeadersData.update()
        return res

    @router.put("/api/headers/{item_id}", tags=[TAG_CLASS])
    @admin_role_authentificated
    async def update_item(self, item_id: int = Path(), item: CommonHeaders = Depends()):
        item_db = await self.get_object_id(item_id)
        res = await self.prepare(item_db)
        if item_db is not None:
            res = await CommonHeadersInDB.update_or_create(item, item_db, ret=res)
            await HTTPHeadersData.update()
        return res


app.include_router(router)


@app.options("/api/headers/list", tags=[TAG_CLASS])
async def options_object_id(response: Response):
    return await set_response_headers(response)


@app.options("/api/headers/{item_id}", tags=[TAG_CLASS])
async def options_item(response: Response):
    return await set_response_headers(response)


@app.options("/api/headers/new", tags=[TAG_CLASS])
async def options_new_item(response: Response):
    return await set_response_headers(response)
