from pathlib import Path

from shared.runtime.contexts.base_runtime_context import (
    BaseRuntimeContext
)

from shared.runtime.artifacts.artifact_paths import (
    get_batch_output_dir,
    get_batch_manifest_path,
    get_batch_final_video_path,
    get_batch_youtube_description_path,
    get_batch_thumbnail_path
)


class BatchRuntimeContext(
    BaseRuntimeContext
):
    def __init__(
            self,
            task,
            worker_id: str,
            workspace_dir: Path,
            artifact_storage,
            batch_id: str,
    ):
        super().__init__(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
        )

        self.batch_id = batch_id

        # =====================================
        # ROOT
        # =====================================

        self.batch_output_dir = (
            get_batch_output_dir(
                batch_id
            )
        )

        self.batch_manifest_path = (
            get_batch_manifest_path(
                batch_id
            )
        )
        # =====================================
        # OUTPUTS
        # =====================================

        self.final_video_path = (
            get_batch_final_video_path(
                batch_id
            )
        )

        self.youtube_description_path = (
            get_batch_youtube_description_path(
                batch_id
            )
        )

        self.thumbnail_path = (
            get_batch_thumbnail_path(
                batch_id
            )
        )

    async def initialize(self):

        batch = self.task.batch

        if not batch:
            raise ValueError(
                "Task has no batch"
            )

        story = batch.story

        if not story:
            raise ValueError(
                "Batch has no story"
            )

        channel = story.channel

        if not channel:
            raise ValueError(
                "Story has no channel"
            )

        self.channel = channel

        self.mc_path = (
            channel.mc_path
        )

        self.mc_name = (
            channel.mc_name
        )

