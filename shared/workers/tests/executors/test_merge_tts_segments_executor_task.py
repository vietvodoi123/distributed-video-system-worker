import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class MergeTtsWorker(
    BaseWorker
):

    capabilities = [
        "ffmpeg"
    ]


async def main():

    worker = MergeTtsWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())