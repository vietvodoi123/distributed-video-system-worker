from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.text.cleaners.cn_cleaner import (
    clean_cn_content
)

from shared.text.cleaners.cn_validator import (
    validate_raw_text, validate_cleaned_chapter
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
        runtime_context: ChapterRuntimeContext
    ):

        # =====================================
        # LOAD FROM DATABASE
        # =====================================

        chapter = (
            await runtime_context
            .api_client
            .get_chapter_text(
                runtime_context.chapter_id
            )
        )


        raw_text = (
            chapter.get(
                "raw_text"
            )
        )


        if not raw_text:

            raise ValueError(
                "raw text is empty"
            )

        # =====================================
        # VALIDATE RAW
        # =====================================

        validate_raw_text(
            raw_text
        )

        # =====================================
        # CLEAN
        # =====================================

        cleaned_text = clean_cn_content(
            raw_text
        )

        # =====================================
        # VALIDATE CLEANED
        # =====================================

        validate_cleaned_chapter(
            cleaned_text
        )


        # =====================================
        # SAVE TO DATABASE
        # =====================================

        await (
            runtime_context
            .api_client
            .update_chapter_text(

                chapter_id=
                runtime_context.chapter_id,

                data={

                    "cleaned_text":
                    cleaned_text
                }
            )
        )


        print(
            "[PreprocessTextExecutor]",
            "saved cleaned_text",
            runtime_context.chapter_number
        )


        # =====================================
        # RESULT
        # =====================================

        return {

            "result": {

                "chapter_id":
                runtime_context.chapter_id,


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

            "disk_io": 0
        }