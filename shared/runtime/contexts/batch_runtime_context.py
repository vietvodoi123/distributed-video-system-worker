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
            worker_id,
            workspace_dir,
            artifact_storage,
            batch_id,
            api_client=None,
    ):
        super().__init__(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
            api_client=api_client,
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

        payload = (
                self.task.payload
                or {}
        )

        channel = (
            payload.get(
                "channel"
            )
        )

        if channel:

            self.channel = channel

            self.mc_path = (
                channel.get(
                    "mc_path"
                )
            )

            self.mc_name = (
                channel.get(
                    "mc_name"
                )
            )

        else:

            self.channel = None

            self.mc_path = None

            self.mc_name = None

