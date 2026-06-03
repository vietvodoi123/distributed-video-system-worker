import time

from datetime import datetime
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_with_progress
)
from shared.runtime.contexts.chapter_runtime_context import (ChapterRuntimeContext)


class MergeAudioIntoVideoExecutor(
    BaseTaskExecutor
):

    CAPABILITIES = [
        "ffmpeg"
    ]

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
        # INPUT PATHS
        # =====================================

        video_input = (

                task.payload.get(
                    "video_path"
                )

                or

                task.payload.get(
                    "video_input"
                )
        )

        audio_input = (

                task.payload.get(
                    "narration_wav_path"
                )

                or

                task.payload.get(
                    "audio_input"
                )
        )

        if not video_input:
            raise ValueError(
                "Missing video_input"
            )

        if not audio_input:
            raise ValueError(
                "Missing audio_input"
            )

        final_video_path = (
            runtime_context.final_video_path
        )

        # =====================================
        # MATERIALIZE
        # =====================================

        local_video = Path(

            await storage.get_local_path(
                video_input,
                runtime_context.workspace_dir
            )
        )

        local_audio = Path(

            await storage.get_local_path(
                audio_input,
                runtime_context.workspace_dir
            )
        )

        # =====================================
        # VALIDATE
        # =====================================

        if not local_video.exists():

            raise FileNotFoundError(
                f"Missing composited video: {local_video}"
            )

        if not local_audio.exists():

            raise FileNotFoundError(
                f"Missing narration audio: {local_audio}"
            )

        # =====================================
        # OUTPUT
        # =====================================

        local_output = (

            runtime_context
            .workspace_dir
            / "final.mp4"
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

            "-i",
            str(local_video),

            "-i",
            str(local_audio),

            "-map",
            "0:v",

            "-map",
            "1:a",

            # ==============================
            # IMPORTANT
            # ==============================

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-shortest",

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
                "Final video not generated"
            )

        if local_output.stat().st_size <= 0:

            raise ValueError(
                "Final video empty"
            )

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(

            final_video_path,

            local_output.read_bytes()
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

            "video_input":
                video_input,

            "audio_input":
                audio_input,

            "output_path":
                final_video_path,

            "video_codec":
                "copy",

            "audio_codec":
                "aac",

            "render_time_seconds":
                round(
                    time.time() - started_at,
                    2
                )
        }

        manifest_path = (

            f"{runtime_context.chapter_dir}"
            f"/video/metadata/"
            f"merge_audio_manifest.json"
        )

        await storage.write_json(

            manifest_path,
            manifest
        )

        print(
            "[MergeAudioIntoVideoExecutor] Completed"
        )

        return {

            "output_path":
            final_video_path,

            "manifest_path":
            manifest_path,

            "result":
            manifest
        }
