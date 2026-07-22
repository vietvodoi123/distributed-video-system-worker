import time
from datetime import datetime

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.static_assets.text_scroll.text_scroll_asset_manager import (
    TextScrollAssetManager
)

from shared.runtime.contexts.chapter_runtime_context import (ChapterRuntimeContext)

class GenerateTextScrollExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context:ChapterRuntimeContext
    ):

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        payload = task.payload or {}
        duration = payload.get('duration')

        if duration is None:
            raise ValueError(
                f"TextScroll No duration provided for task {task} chapter={task.chapter_number}"
            )

        # =====================================
        # LOCAL OUTPUT
        # =====================================

        local_output = (
            runtime_context.workspace_dir
            / "text_scroll.mp4"
        )

        # =====================================
        # STATIC ASSET MANAGER
        # =====================================

        manager = (
            TextScrollAssetManager()
        )

        manager.create_duration_variant(

            duration=duration,

            output_path=local_output
        )

        # =====================================
        # VALIDATE OUTPUT
        # =====================================

        if not local_output.exists():

            raise FileNotFoundError(
                "Failed to generate "
                "text scroll video"
            )

        # =====================================
        # UPLOAD
        # =====================================

        video_bytes = (
            local_output.read_bytes()
        )

        await storage.write_bytes(

            runtime_context
            .text_scroll_video_path,

            video_bytes
        )

        print(
            "[GenerateTextScrollExecutor] "
            f"Uploaded: "
            f"{runtime_context.text_scroll_video_path}"
        )

        # =====================================
        # MANIFEST
        # =====================================


        print(
            "[GenerateTextScrollExecutor] "
            "Completed"
        )

        # =====================================
        # RESULT
        # =====================================

        return {

            "output_path": (
                runtime_context
                .text_scroll_video_path
            ),


        }

