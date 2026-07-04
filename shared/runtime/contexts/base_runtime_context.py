from abc import ABC
from pathlib import Path
from shared.contracts.task_dto import (
    TaskDto
)

task: TaskDto
from shared.runtime.storage.base_artifact_storage import (
    BaseArtifactStorage
)


class BaseRuntimeContext(ABC):

    def __init__(
            self,
            task: TaskDto,
            worker_id: str,
            workspace_dir: Path,
            artifact_storage: BaseArtifactStorage,
            api_client=None,
    ):
        self.task = task

        self.worker_id = worker_id

        self.workspace_dir = workspace_dir

        self.artifact_storage = (
            artifact_storage
        )

        self.api_client = api_client

        self.channel = None

        self.mc_path = None

        self.mc_name = None

    async def initialize(self):
        raise NotImplementedError

    async def close(self):
        pass