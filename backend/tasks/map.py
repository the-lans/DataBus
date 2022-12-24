from backend.models.map import HTTPMapInDB
from backend.db.base import execute

HTTP_MAP_DICT = {}
HTTP_MAP_OBJ = {}


async def map_update() -> dict:
    global HTTP_MAP_DICT
    global HTTP_MAP_OBJ

    HTTP_MAP_DICT = {}
    HTTP_MAP_OBJ = {}
    for obj in await execute(HTTPMapInDB.select()):
        HTTP_MAP_DICT[obj.id] = await obj.dict
        HTTP_MAP_OBJ[obj.id] = obj
    return HTTP_MAP_DICT


def filter_proxy_url(queue: str, method: str) -> dict:
    proxy_urls = {}
    for key, item in HTTP_MAP_OBJ.items():
        if item.queue == queue and item.method == method:
            proxy_urls[key] = item
    return proxy_urls
