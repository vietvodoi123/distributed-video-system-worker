import asyncio
from pathlib import Path
from shared.config.settings import settings

from shared.runtime.workers.base_worker import (
    BaseWorker
)
ROOT = Path(__file__).resolve().parent

model_path = ROOT / "shared/data/model/ngochuyennew.onnx"
config_path = ROOT / "shared/data/model/ngochuyennew.onnx.json"

class Worker(BaseWorker):

    def __init__(self,model_path,config_path):

        super().__init__(model_path,config_path)

        self.capabilities = settings.capabilities


async def main():
    worker = Worker(model_path,config_path)

    await worker.start()


if __name__ == "__main__":
    ROOT = Path(__file__).parent

    asyncio.run(main())
