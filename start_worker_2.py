import asyncio
from pathlib import Path
from shared.config.settings import settings

from shared.runtime.workers.base_worker import (
    BaseWorker
)


class Worker(BaseWorker):

    def __init__(self,model_path,config_path):

        super().__init__(model_path,config_path)

        self.capabilities = settings.capabilities


async def main():
    model_path = r'C:\Users\HLC\PycharmProjects\distributed-video-system-worker\shared\data\model\ngochuyennew.onnx'
    config_path = r'C:\Users\HLC\PycharmProjects\distributed-video-system-worker\shared\data\model\ngochuyennew.onnx.json'

    worker = Worker(model_path,config_path)

    await worker.start()


if __name__ == "__main__":
    ROOT = Path(__file__).parent

    asyncio.run(main())
