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
    ):
        self.task = task

        self.worker_id = worker_id

        self.workspace_dir = workspace_dir

        self.artifact_storage = (
            artifact_storage
        )

        self.channel = None

        self.mc_path = None

        self.mc_name = None

    async def initialize(self):
        raise NotImplementedError

    # @property
    # def upstream_task(self):
    #
    #     return getattr(
    #         self.task,
    #         "depends_on_task",
    #         None
    #     )

    # @property
    # def upstream_output_path(self):
    #
    #     upstream = self.upstream_task
    #
    #     if not upstream:
    #         return None
    #
    #     return upstream.output_path

    # @property
    # def upstream_manifest_path(self):
    #
    #     upstream = self.upstream_task
    #
    #     if not upstream:
    #         return None
    #
    #     return upstream.manifest_path

    async def close(self):
        pass