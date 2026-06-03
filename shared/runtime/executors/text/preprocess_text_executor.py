import re

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.text.cleaners.cn_cleaner import (
    clean_cn_content
)
from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)

class PreprocessTextExecutor(
    BaseTaskExecutor
):

    task_type = "preprocess_text"

    async def execute(
        self,
        task,
        runtime_context:ChapterRuntimeContext
    ):
        print(
            "[PREPROCESS PAYLOAD]",
            task.payload
        )
        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # INPUT
        # =====================================

        input_path = (
            task.payload.get(
                "input_path"
            )
        )

        raw_text = await storage.read_text(
            input_path
        )

        if not raw_text:

            raise ValueError(
                "raw text is empty"
            )

        # =====================================
        # CLEAN
        # =====================================

        cleaned_text = clean_cn_content(
            raw_text
        )

        # =====================================
        # OUTPUT
        # =====================================

        output_path = (
            runtime_context
            .preprocess_text_path
        )

        await storage.write_text(
            output_path,
            cleaned_text
        )

        # =====================================
        # RESULT
        # =====================================

        return {

            "result": {

                "input_path":
                    input_path,

                "output_path":
                    output_path,

                "raw_length":
                    len(raw_text),

                "cleaned_length":
                    len(cleaned_text),
                "metrics": {

                    "input_length":
                        len(raw_text),

                    "output_length":
                        len(cleaned_text)
                }
            },

            "output_path":
                output_path
        }

    def get_resource_requirements(
            self,
            task,runtime_context
    ):
        return {

            "cpu": 1,

            "ram": 1,

            "gpu": 0,

            "network": 0,

            "disk_io": 1
        }