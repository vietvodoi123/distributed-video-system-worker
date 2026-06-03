import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class TextScrollVdWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg"
    ]


async def main():

    worker = TextScrollVdWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())