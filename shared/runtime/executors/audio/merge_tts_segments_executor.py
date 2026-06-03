import time
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.audio.utils.audio_concat import (
    concat_wav_files
)
from shared.contracts.artifact_models.timeline_artifact import (
    TimelineArtifact,
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
                "No TTS segments found"
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
                    "audio_path"
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

        duration = round(
            time.time() - started_at,
            2
        )

        print(

            "[MergeTtsSegmentsExecutor] "

            f"Merged {len(local_files)} "

            f"segments"
        )

        # =====================================
        # timeline
        # =====================================
        timeline_segments: list[TimelineSegment] = []

        current_time = 0.0

        for segment in segments:
            duration = (
                segment["duration"]
            )

            start_time = current_time

            end_time = (
                    current_time + duration
            )

            timeline_segments.append(

                TimelineSegment(

                    line_index=
                    segment[
                        "line_index"
                    ],

                    text=
                    segment[
                        "text"
                    ],

                    start_time=
                    round(start_time, 3),

                    end_time=
                    round(end_time, 3),

                    duration=
                    round(duration, 3),

                    audio_path=
                    segment[
                        "audio_path"
                    ]
                )
            )

            current_time = end_time

        await storage.write_json(

            runtime_context.timeline_path,

            {
                "total_duration":
                    round(current_time, 3),

                "total_segments":
                    len(timeline_segments),

                "segments": [

                    {
                        "line_index":
                            s.line_index,

                        "text":
                            s.text,

                        "start_time":
                            s.start_time,

                        "end_time":
                            s.end_time,

                        "duration":
                            s.duration,

                        "audio_path":
                            s.audio_path
                    }

                    for s in timeline_segments
                ]
            }
        )
        # =====================================
        # RESULT
        # =====================================

        return {

            "output_path": (
                runtime_context
                .narration_wav_path
            ),

            "manifest_path": (
                runtime_context
                .timeline_path
            ),

            "result": {

                "success": True,

                "merged_segments": (
                    len(local_files)
                ),

                "duration_seconds": (
                    current_time
                ),

                "timeline_path": (
                    runtime_context
                    .timeline_path
                ),
                "metrics": {

                    "output_segments":
                        len(local_files),

                    "duration_seconds":
                        current_time,

                    "executor_duration":
                        duration
                }
            }
        }
