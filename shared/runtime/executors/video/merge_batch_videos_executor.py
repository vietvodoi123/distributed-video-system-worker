from pathlib import Path
import subprocess
import time
from datetime import datetime


from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.contracts.enums.task_types import (
    MERGE_AUDIO_INTO_VIDEO
)

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_with_progress
)

from shared.runtime.contexts.batch_runtime_context import (BatchRuntimeContext)

class MergeBatchVideosExecutor(
    BaseTaskExecutor
):

    CAPABILITIES = [
        "ffmpeg"
    ]

    async def execute(
        self,
        task,
        runtime_context:BatchRuntimeContext,
    ):

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # LOAD CHAPTER TASKS
        # =====================================

        video_paths = (
            task.payload.get(
                "video_paths",
                []
            )
        )

        if not video_paths:
            raise ValueError(
                "No chapter videos found"
            )


        # =====================================
        # MATERIALIZE LOCAL FILES
        # =====================================

        local_video_paths = []

        for remote_video_path in video_paths:

            remote_video_path = (
                remote_video_path
            )

            print(
                "[MergeBatchVideosExecutor] "
                f"Materializing: "
                f"{remote_video_path}"
            )

            local_path = Path(

                await storage.get_local_path(
                    remote_video_path,
                    runtime_context.workspace_dir
                )
            )
            if not local_path.exists():

                raise FileNotFoundError(
                    f"Missing local video: "
                    f"{local_path}"
                )

            local_video_paths.append(
                local_path
            )

        # =====================================
        # CONCAT FILE
        # =====================================

        concat_file = (

            runtime_context.workspace_dir
            / "concat.txt"
        )

        concat_lines = []

        for video_path in local_video_paths:

            safe_path = (
                str(video_path.resolve())
                .replace("\\", "/")
                .replace("'", r"'\''")
            )

            concat_lines.append(
                f"file '{safe_path}'"
            )

        concat_file.write_text(

            "\n".join(concat_lines),

            encoding="utf-8"
        )

        print(
            "[MergeBatchVideosExecutor] "
            f"Concat file created: "
            f"{concat_file}"
        )

        # =====================================
        # OUTPUT
        # =====================================

        local_output = (

            runtime_context.workspace_dir
            / "merged_batch.mp4"
        )

        remote_output = (
            runtime_context.final_video_path
        )

        # =====================================
        # FFMPEG
        # =====================================

        cmd = [

            "ffmpeg",

            "-y",

            "-hide_banner",

            "-loglevel",
            "info",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            str(concat_file),

            "-c",
            "copy",

            "-movflags",
            "+faststart",

            str(local_output)
        ]

        run_ffmpeg_with_progress(
            cmd
        )

        # =====================================
        # VALIDATE OUTPUT
        # =====================================

        if not local_output.exists():

            raise FileNotFoundError(
                "Merged batch video not generated"
            )

        if local_output.stat().st_size <= 0:

            raise ValueError(
                "Merged batch video empty"
            )

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(

            remote_output,

            local_output.read_bytes()
        )

        print(
            "[MergeBatchVideosExecutor] "
            f"Uploaded merged video: "
            f"{remote_output}"
        )

        # =====================================
        # MANIFEST
        # =====================================

        manifest = {

            "success": True,

            "executor":
            self.__class__.__name__,

            "generated_at":
            datetime.utcnow().isoformat(),

            "chapter_count":
            len(video_paths),

            "output_path":
            remote_output,

            "render_time_seconds":
            round(
                time.time()
                - started_at,
                2
            )
        }

        manifest_path = (

            f"{runtime_context.batch_output_dir}"
            f"/metadata/"
            f"merge_batch_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
        )

        print(
            "[MergeBatchVideosExecutor] Completed"
        )

        # =====================================
        # RETURN
        # =====================================

        return {

            "output_path":
            remote_output,

            "manifest_path":
            manifest_path,

            "result":
            manifest
        }

    def get_resource_requirements(
            self,
            task,runtime_context
    ):

        chapter_count = (
            task.payload.get(
                "chapter_count",
                10
            )
        )

        factor = max(
            1,
            chapter_count / 10
        )

        return {

            "cpu": min(
                40,
                10 * factor
            ),

            "ram": min(
                32,
                6 * factor
            ),

            "gpu": 0,

            "network": 0,

            "disk_io": min(
                50,
                15 * factor
            )
        }