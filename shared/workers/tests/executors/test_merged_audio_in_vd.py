import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class MGvpVDWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg"
    ]


async def main():

    worker = MGvpVDWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())