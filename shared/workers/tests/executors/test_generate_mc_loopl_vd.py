import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class MCLoopVDWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg"
    ]


async def main():

    worker = MCLoopVDWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())