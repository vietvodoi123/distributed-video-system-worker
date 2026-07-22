import time
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.audio.utils.audio_concat import (
    concat_wav_files
)
from shared.contracts.artifact_models.timeline_artifact import (
    TimelineSegment
)
from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)
class MergeTtsSegmentsExecutor(
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

        merge_payload = task.payload or {}
        segments = merge_payload.get(
            "segments",
            []
        )
        if not segments:
            raise ValueError(
                f"No TTS segments found "
                f"chapter={task.chapter_id} "
                f"task={task.id}"
            )
        segments.sort(
            key=lambda x:
            x["line_index"]
        )

        # =====================================
        # DOWNLOAD WAVS
        # =====================================

        local_files = []

        for segment in segments:

            output_path = (
                segment[
                    "output_path"
                ]
            )

            exists = await storage.exists(
                output_path
            )

            if not exists:

                raise RuntimeError(

                    f"Missing artifact: "
                    f"{output_path}"
                )

            local_path = await (
                storage.get_local_path(
                    output_path,
                    runtime_context.workspace_dir
                )
            )
            local_files.append(
                local_path
            )

        # =====================================
        # OUTPUT
        # =====================================

        merged_local_path = str(

            Path(
                runtime_context.workspace_dir
            ) / "merged.wav"
        )

        # =====================================
        # CONCAT
        # =====================================

        await concat_wav_files(

            input_files=
            local_files,

            output_file=
            merged_local_path,

            workspace_dir=
            runtime_context.workspace_dir
        )

        # =====================================
        # READ MERGED
        # =====================================

        with open(
            merged_local_path,
            "rb"
        ) as f:

            merged_bytes = f.read()

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(

            runtime_context
            .narration_wav_path,

            merged_bytes
        )

        print(

            "[MergeTtsSegmentsExecutor] "

            f"Merged {len(local_files)} "

            f"segments"
        )

        # =====================================
        # BUILD SEGMENTS
        # =====================================

        result_segments = []

        current_time = 0.0

        for segment in segments:
            segment_duration = round(
                segment["duration"],
                3,
            )

            start_time = round(
                current_time,
                3,
            )

            end_time = round(
                current_time + segment_duration,
                3,
            )

            result_segments.append({

                "line_index":
                    segment["line_index"],

                "line_text":
                    segment["line_text"],

                "start_time":
                    start_time,

                "end_time":
                    end_time,

                "duration":
                    segment_duration,
            })

            current_time = end_time

        # =====================================
        # RESULT
        # =====================================

        return {

            "output_path":
                runtime_context.narration_wav_path,

            "duration":
                round(current_time, 3),

            "segments":
                result_segments,

        }
