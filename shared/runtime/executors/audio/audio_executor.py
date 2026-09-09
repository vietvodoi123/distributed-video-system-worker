import time
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor,
)

from shared.runtime.executors.audio.service.tts_service import (
    TTSService,
)

from shared.runtime.executors.audio.service.models import (
    TTSOptions,
)

from shared.runtime.executors.audio.utils.audio_concat import (
    concat_wav_files,
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext,
)


class AudioExecutor(
    BaseTaskExecutor,
):

    def __init__(
        self,
        *,
        tts_service: TTSService,
    ):
        self.tts_service = tts_service

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext,
    ):

        started_at = time.time()

        api = (
            runtime_context
            .api_client
        )

        storage = (
            runtime_context
            .artifact_storage
        )

        chapter_id = (
            task.chapter_id
        )

        # =====================================
        # GET TRANSLATED TEXT
        # =====================================

        chapter_data = await api.get_chapter_text(
            chapter_id
        )

        if not chapter_data:
            raise RuntimeError(
                f"Cannot load chapter text: "
                f"chapter={chapter_id}"
            )

        translate_text = (
            chapter_data.get(
                "translated_text"
            )
        )

        if not translate_text:
            raise RuntimeError(
                f"Chapter has no translated_text: "
                f"chapter={chapter_id}"
            )

        # =====================================
        # SPLIT LINES
        # =====================================

        raw_lines = (
            translate_text.split("\n")
        )

        lines = [
            line.strip()
            for line in raw_lines
            if line.strip()
        ]

        if not lines:
            raise RuntimeError(
                f"Translated text contains no "
                f"usable lines: chapter={chapter_id}"
            )

        print(
            "[AudioExecutor] "
            f"Chapter={chapter_id} "
            f"Lines={len(lines)}"
        )

        # =====================================
        # TTS OPTIONS
        # =====================================

        options = TTSOptions(
            speed=1.5,
            volume=1.0,
            sentence_silence=0.0,
        )

        # =====================================
        # GENERATE TTS
        # =====================================

        segment_files = []
        segments = []

        for line_index, line_text in enumerate(lines):

            output_file = (
                Path(
                    runtime_context.workspace_dir
                )
                / f"tts_line_{line_index}.wav"
            )

            result = (
                self.tts_service.synthesize_text(
                    text=line_text,
                    output_file=output_file,
                    options=options,
                )
            )

            segment_files.append(
                output_file
            )

            segments.append({
                "line_index":
                    line_index,

                "line_text":
                    line_text,

                "output_path":
                    str(output_file),

                "duration":
                    result.duration,
            })

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
            segment_files,

            output_file=
            merged_local_path,

            workspace_dir=
            runtime_context.workspace_dir,
        )

        # =====================================
        # READ MERGED
        # =====================================

        with open(
            merged_local_path,
            "rb",
        ) as f:

            merged_bytes = f.read()

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(

            runtime_context.narration_wav_path,

            merged_bytes,
        )

        # =====================================
        # BUILD TIMELINE SEGMENTS
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

        duration = round(
            current_time,
            3,
        )

        elapsed = round(
            time.time() - started_at,
            3,
        )

        print(
            "[AudioExecutor] "
            f"Generated {len(segments)} segments "
            f"duration={duration}s "
            f"elapsed={elapsed}s"
        )

        return {

            "output_path":
                runtime_context.narration_wav_path,

            "duration":
                duration,

            "segments":
                result_segments,

        }