from multiprocessing import Event
import asyncio
import logging


class BaseProcessing:
    def __init__(self, timeout=0.1):
        self.__stop_polling = Event()
        self.__timeout_polling = timeout

    async def polling(self):
        pass

    async def infinity_polling(self):
        while not self.__stop_polling.is_set():
            try:
                await self.polling()
                await asyncio.sleep(self.__timeout_polling)
            except (KeyboardInterrupt, SystemExit):
                logging.warning('KeyboardInterrupt received.')
                self.stop_polling()
                break
            except Exception as e:
                logging.error(e)

    def stop_polling(self):
        self.__stop_polling.set()


async def task_processing(proc: BaseProcessing):
    task = asyncio.create_task(proc.infinity_polling())
    await task


def processing(proc: BaseProcessing):
    asyncio.run(task_processing(proc))
