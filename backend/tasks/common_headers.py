from backend.models.common_headers import CommonHeadersInDB
from backend.db.base import execute

HTTP_HEADERS_DICT = {}
HTTP_HEADERS_OBJ = {}


async def headers_update() -> dict:
    global HTTP_HEADERS_DICT
    global HTTP_HEADERS_OBJ

    HTTP_HEADERS_DICT = {}
    HTTP_HEADERS_OBJ = {}
    for obj in await execute(CommonHeadersInDB.select()):
        HTTP_HEADERS_DICT[obj.id] = await obj.dict
        HTTP_HEADERS_OBJ[obj.id] = obj
    return HTTP_HEADERS_DICT


def filter_headers(queue: str) -> dict:
    result = {}
    for key, item in HTTP_HEADERS_OBJ.items():
        if item.queue == queue:
            result[key] = item
    return result
