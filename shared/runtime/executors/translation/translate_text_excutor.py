# shared/runtime/executors/translation/translate_text_executor.py

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.translation.services.moxhi_translate_service import (
    MoxhiTranslateService
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)


class TranslateTextExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):

        api = (
            runtime_context
            .api_client
        )

        chapter_id = task.chapter_id

        chapter = await api.get_chapter_text(
            chapter_id
        )

        cleaned_text = chapter.get(
            "cleaned_text"
        )

        if not cleaned_text:
            return {
                "result": {
                    "translated_text": ""
                }
            }

        translate_service = (
            MoxhiTranslateService()
        )

        chapter_translated = (
            await translate_service.translate(
                cleaned_text
            )
        )

        await api.update_chapter_text(
            chapter_id=chapter_id,
            data={
                "translated_text":
                    chapter_translated
            }
        )

        print(
            f"translated text chapter "
            f"{chapter_id}"
        )

        return {
                "translated_text": chapter_translated,

        }