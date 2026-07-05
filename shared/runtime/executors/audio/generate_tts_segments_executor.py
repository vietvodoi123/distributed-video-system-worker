from datetime import datetime
import time
import uuid

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.audio.utils.line_splitter import (
    split_script_lines
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)


class GenerateTtsSegmentsExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # LOAD SCRIPT FROM DB
        # =====================================

        chapter = (
            await runtime_context
            .api_client
            .get_chapter_text(
                runtime_context.chapter_id
            )
        )

        script_text = (
            chapter.get(
                "final_script"
            )
            or
            chapter.get(
                "translated_text"
            )
        )

        if not script_text:

            raise ValueError(
                "script text is empty"
            )

        script_text = (
            script_text.strip()
        )

        # =====================================
        # SPLIT LINE
        # =====================================

        lines = split_script_lines(
            script_text
        )

        if not lines:

            raise ValueError(
                "No valid script lines found"
            )

        # =====================================
        # TASK GROUP
        # =====================================

        task_group = (
            f"tts_{uuid.uuid4().hex}"
        )

        voice = (
            task.payload.get(
                "voice",
                "default"
            )
        )

        # =====================================
        # CREATE SEGMENTS
        # =====================================

        segments = []

        for line in lines:

            output_name = (
                f"{task_group}_"
                f"{line.line_index:04d}.wav"
            )

            output_path = (

                f"{runtime_context.chapter_dir}"

                f"/tts/audio/"

                f"{output_name}"
            )


            segments.append({

                "line_index":
                line.line_index,

                "text":
                line.text,

                "voice":
                voice,

                "output_name":
                output_name,

                "output_path":
                output_path
            })


        # =====================================
        # MANIFEST STILL MINIO
        # =====================================

        manifest = {

            "success":
            True,

            "executor":
            self.__class__.__name__,

            "stage":
            "generate_tts_segments",

            "task_group":
            task_group,

            "total_segments":
            len(segments),

            "generated_at":
            datetime.utcnow().isoformat(),

            "segments":
            segments
        }


        manifest_path = (

            f"{runtime_context.chapter_dir}"

            f"/tts/metadata/"

            f"tts_generation_manifest.json"
        )


        await storage.write_json(

            manifest_path,

            manifest
        )


        duration = round(
            time.time() - started_at,
            2
        )


        print(
            "[GenerateTtsSegmentsExecutor]",
            f"Prepared {len(segments)} segments"
        )


        return {

            "manifest_path":
            manifest_path,


            "result": {

                "task_group":
                task_group,


                "segments":
                segments,


                "total_segments":
                len(segments),


                "duration_seconds":
                duration,


                "metrics": {

                    "output_segments":
                    len(segments),


                    "output_length":
                    len(script_text),


                    "executor_duration":
                    duration
                }
            }
        }


    def get_resource_requirements(
        self,
        task,
        runtime_context
    ):

        return {

            "cpu": 1,

            "ram": 1,

            "gpu": 0,

            "network": 1,

            "disk_io": 1,

            "queue_pressure": 5
        }