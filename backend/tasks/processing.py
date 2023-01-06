from typing import Optional
from collections import AsyncIterable
from aioredis import Redis

from backend.tasks.base import BaseProcessing
from backend.library.redis import get_aclient
from backend.models.request_message import RequestMessage
from backend.config import REDIS_QUEUE


class Processing(BaseProcessing):
    _redis_conn: Optional[Redis] = None

    def __init__(self, timeout=0.1):
        super().__init__(timeout)

    async def ainit(self):
        await super().ainit()
        Processing._redis_conn = await get_aclient()

    @staticmethod
    async def queue_pop(queue: str) -> AsyncIterable[RequestMessage]:
        while True:
            data = await Processing._redis_conn.lpop(queue)
            if data:
                yield RequestMessage.loads(data)
            else:
                break

    @staticmethod
    async def queue_push(queue: str, message: RequestMessage):
        await Processing._redis_conn.rpush(queue, message.dumps())

    @staticmethod
    async def check_queue(queue: str):
        llen = await Processing._redis_conn.llen(queue)
        if llen == 0:
            pipeline = Processing._redis_conn.pipeline(transaction=True)
            pipeline.multi()
            await pipeline.llen(queue)
            await pipeline.srem(REDIS_QUEUE, queue)
            res = await pipeline.execute()
            if res[0] > 0:
                await Processing._redis_conn.sadd(REDIS_QUEUE, queue)

    async def polling(self):
        queues = [queue.decode('utf8') for queue in await Processing._redis_conn.smembers(REDIS_QUEUE)]
        for queue in queues:
            async for message in self.queue_pop(queue):
                message.set_proxy_url(queue)
                await message.send_requests()
                if not message.processed:
                    await self.queue_push(queue, message)
            await self.check_queue(queue)
