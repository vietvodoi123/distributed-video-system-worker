import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class RenderTWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg","puppeteer"
    ]


async def main():

    worker = RenderTWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())