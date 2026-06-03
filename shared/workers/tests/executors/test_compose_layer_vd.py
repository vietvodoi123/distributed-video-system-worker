import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class CPVDWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg"
    ]


async def main():

    worker = CPVDWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())