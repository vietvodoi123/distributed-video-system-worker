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

        # =====================================
        # TIMELINE
        # =====================================

        timeline_path = (
            task.payload.get(
                "timeline_path"
            )
        )

        if not timeline_path:
            raise ValueError(
                "Missing timeline_path"
            )

        timeline_data = (
            await storage.read_json(
                timeline_path
            )
        )

        segments = timeline_data.get(
            "segments",
            []
        )

        if not segments:

            raise ValueError(
                "Timeline segments empty"
            )

        # =====================================
        # DURATION
        # =====================================

        duration = 0.0

        for segment in segments:

            duration = max(
                duration,
                segment["end_time"]
            )

        if duration <= 0:

            raise ValueError(
                "Invalid timeline duration"
            )

        print(
            "[GenerateMcLoopExecutor] "
            f"Target duration: "
            f"{duration:.2f}s"
        )

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
                runtime_context.mc_path,

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

        # =====================================
        # MANIFEST
        # =====================================

        duration_seconds = round(
            time.time() - started_at,
            2
        )
        metrics = {

            "video_duration_seconds":
                duration,

            "executor_duration":
                duration_seconds
        }
        manifest = {

            "success": True,

            "executor": (
                self.__class__.__name__
            ),

            "generated_at": (
                datetime.utcnow()
                .isoformat()
            ),

            "mc_name": (
                runtime_context.mc_name
            ),

            "mc_path": (
                runtime_context.mc_path
            ),

            "target_duration": (
                duration
            ),

            "output_path": (
                runtime_context
                .mc_loop_video_path
            ),

            "duration_seconds": (
                duration_seconds
            )
        }

        manifest_path = (
            f"{runtime_context.chapter_dir}"
            f"/video/metadata/"
            f"mc_loop_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
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
            ),

            "manifest_path": (
                manifest_path
            ),

            "result": {"manifest": manifest,
                       "metrics": metrics},
        }
