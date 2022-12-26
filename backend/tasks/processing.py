from backend.tasks.base import BaseProcessing
from backend.library.redis import redis_call
from backend.models.request_message import RequestMessage
from backend.config import REDIS_QUEUE


class Processing(BaseProcessing):
    def __init__(self, timeout=0.1):
        super().__init__(timeout)

    @staticmethod
    async def queue_pop(queue: str) -> RequestMessage:
        data = await redis_call("lpop", queue)
        return RequestMessage.loads(data) if data else None

    @staticmethod
    async def queue_push(queue: str, message: RequestMessage):
        await redis_call("rpush", queue, message.dumps())

    @staticmethod
    async def check_queue(queue: str):
        llen = await redis_call("llen", queue)
        if llen == 0:
            await redis_call("multi")
            await redis_call("llen", queue)
            await redis_call("srem", REDIS_QUEUE, queue)
            res = await redis_call("exec")
            if res[0] > 0:
                await redis_call("sadd", REDIS_QUEUE, queue)

    async def polling(self):
        queues = await redis_call("smembers", REDIS_QUEUE)
        for queue in queues:
            while True:
                message = await self.queue_pop(queue)
                if message is None:
                    break
                message.set_proxy_url(queue)
                await message.send_requests()
                if not message.processed:
                    await self.queue_push(queue, message)
            await self.check_queue(queue)
