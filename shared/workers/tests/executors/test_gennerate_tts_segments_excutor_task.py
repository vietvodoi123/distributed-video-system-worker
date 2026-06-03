import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class TTsLineWorker(
    BaseWorker
):

    capabilities = [
        "tts", # rồi sau này phải sửa lại thành android
    ]


async def main():

    worker = TTsLineWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())