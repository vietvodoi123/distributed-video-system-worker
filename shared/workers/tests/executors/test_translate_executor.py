import asyncio

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class CrawlWorker(
    BaseWorker
):

    capabilities = [
        "network",
    ]


async def main():

    worker = CrawlWorker()

    await worker.start()


if __name__ == "__main__":

    asyncio.run(main())