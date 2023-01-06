from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Request, Path, Query

from backend.app import app
from backend.api.base import BaseAppAuth
from backend.library.redis import redis_call
from backend.library.api import parse_api_list, parse_api_exclude


router = InferringRouter()
TAG_CLASS = "RedisApp"


@cbv(router)
class RedisApp(BaseAppAuth):
    @classmethod
    async def prepare(cls, obj_db):
        res = await super().prepare(obj_db)
        if not isinstance(obj_db, bool):
            if isinstance(obj_db, bytes):
                res.update({"response": obj_db.decode('utf8')})
            else:
                res.update({"response": str(obj_db)})
        return res

    @staticmethod
    def parse(req: Request):
        return req.query_params.getlist('args'), parse_api_exclude(dict(req.query_params), {'args'})

    @router.get("/api/redis/{cmd}", tags=[TAG_CLASS])
    async def get_redis(self, cmd: str = Path(), args: list[str] = Query()):
        return await self.prepare(await redis_call(cmd, *parse_api_list(args)))

    @router.post("/api/redis/{cmd}", tags=[TAG_CLASS])
    async def post_redis(self, cmd: str, req: Request):
        args, kwargs = self.parse(req)
        return await self.prepare(await redis_call(cmd, *parse_api_list(args), **kwargs))

    @router.put("/api/redis/{cmd}", tags=[TAG_CLASS])
    async def put_redis(self, cmd: str, req: Request):
        args, kwargs = self.parse(req)
        return await self.prepare(await redis_call(cmd, *parse_api_list(args), **kwargs))

    @router.delete("/api/redis/{cmd}", tags=[TAG_CLASS])
    async def delete_redis(self, cmd: str = Path(), args: list[str] = Query()):
        return await self.prepare(await redis_call(cmd, *parse_api_list(args)))


app.include_router(router)
