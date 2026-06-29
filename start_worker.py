import asyncio
import subprocess
import os
from pathlib import Path
from shared.config.settings import settings

from shared.runtime.workers.base_worker import (
    BaseWorker
)
from shared.utils.settings import (
    load_yaml_settings
)
from shared.utils.ffmpeg import setup_ffmpeg


cfg = load_yaml_settings()

class Worker(BaseWorker):

    def __init__(self):

        super().__init__()

        self.capabilities = settings.capabilities


async def main():

    worker = Worker()

    await worker.start()


if __name__ == "__main__":
    # setup_ffmpeg()
    # subprocess.run(
    #     ["ffmpeg", "-version"],
    #     capture_output=True
    # )
    ROOT = Path(__file__).parent



    asyncio.run(main())
