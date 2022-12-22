from backend.models.map import HTTPMapInDB
from backend.db.base import execute

HTTP_MAP_DICT = {}


async def map_update():
    global HTTP_MAP_DICT
    HTTP_MAP_DICT = {obj.id: await obj.dict for obj in await execute(HTTPMapInDB.select())}
    return HTTP_MAP_DICT
