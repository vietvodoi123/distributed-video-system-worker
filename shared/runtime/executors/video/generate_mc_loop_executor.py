import time

from datetime import datetime

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.static_assets.mc_loop.mc_loop_asset_manager import (
    McLoopAssetManager
)

from shared.runtime.contexts.chapter_runtime_context import (ChapterRuntimeContext)


class GenerateMcLoopExecutor(
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




        mc_path = payload.get("mc_path")

        if not mc_path:
            raise ValueError(
                "Missing channel.mc_path in task payload"
            )

        mc_name = payload.get("mc_name")


        # =====================================
        # DURATION
        # =====================================

        duration = payload.get("duration")

        # =====================================
        # LOCAL OUTPUT
        # =====================================

        local_output = (
            runtime_context.workspace_dir
            / "mc_loop.mp4"
        )

        # =====================================
        # ASSET MANAGER
        # =====================================

        manager = (
            McLoopAssetManager(

                mc_path=
                mc_path,

                artifact_storage=
                storage
            )
        )

        await manager.create_duration_variant(

            duration=duration,

            output_path=local_output
        )

        # =====================================
        # VALIDATE OUTPUT
        # =====================================

        if not local_output.exists():

            raise FileNotFoundError(
                "Failed to generate "
                "mc loop video"
            )
        size = local_output.stat().st_size
        print("mc_loop.mp4 size: {}".format(size))
        # =====================================
        # UPLOAD
        # =====================================

        video_bytes = (
            local_output.read_bytes()
        )

        await storage.write_bytes(

            runtime_context
            .mc_loop_video_path,

            video_bytes
        )

        print(
            "[GenerateMcLoopExecutor] "
            f"Uploaded: "
            f"{runtime_context.mc_loop_video_path}"
        )

        print(
            "[GenerateMcLoopExecutor] "
            "Completed"
        )

        # =====================================
        # RESULT
        # =====================================

        return {

            "output_path": (
                runtime_context
                .mc_loop_video_path
            )
        }
