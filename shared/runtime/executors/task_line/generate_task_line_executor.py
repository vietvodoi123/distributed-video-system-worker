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


class GenerateLineTaskExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):

        started_at = time.time()

        # =====================================
        # LOAD TEXT FROM DB
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
                "translated text is empty"
            )


        script_text = (
            script_text.strip()
        )


        # =====================================
        # SPLIT
        # =====================================

        lines = split_script_lines(
            script_text
        )


        if not lines:

            raise ValueError(
                "No valid script lines found"
            )


        # =====================================
        # CONFIG
        # =====================================

        task_group = (
            f"tts_{uuid.uuid4().hex}"
        )


        voice = (

            task.payload.get(
                "voice"
            )

            or

            "vi-vn-x-vie-local"
        )


        # =====================================
        # BUILD LINE TASKS
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


                "line_text":
                    line.text,


                "voice":
                    voice,


                "output_path":
                    output_path
            })


        duration = round(

            time.time()

            -

            started_at,

            2
        )


        print(

            "[GenerateLineTaskExecutor]",

            f"Prepared {len(segments)} line tasks"
        )


        return {

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


