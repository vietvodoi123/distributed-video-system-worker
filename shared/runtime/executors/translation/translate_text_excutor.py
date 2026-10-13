import re

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.translation.services.moxhi_translate_service import (
    MoxhiTranslateService
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)


def filter_corrupted_translation_lines(text: str) -> str:
    """
    Loại bỏ các dòng chứa mã byte rác hoặc domain bị lỗi dịch:
    - Bắt dấu hiệu '><' (hai thẻ dấu ngoặc nhọn đấu đầu nhau như <0xD0><0xB2>)
    - Bắt mã byte hex <0x..>
    - Bắt dòng chỉ chứa domain còn sót lại
    """
    if not text:
        return ""

    hex_byte_pattern = re.compile(r"<0x[0-9a-fA-F]{2}>")
    domain_line_pattern = re.compile(r"(?i)^[a-z0-9\-_.]+\.(?:com|tw|net|org|cn|cc|xyz|top)$")
    clean_lines = []

    for line in text.splitlines():
        line_stripped = line.strip()

        # 1. Bắt signature '><' (hai thẻ byte đụng đầu nhau)
        if "><" in line_stripped:
            continue

        # 2. Bắt mã byte hex lẻ <0x..>
        if hex_byte_pattern.search(line_stripped):
            continue

        # 3. Bắt dòng chỉ là domain rác sót lại
        if domain_line_pattern.match(line_stripped):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


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

        chapter_translated = filter_corrupted_translation_lines(
            chapter_translated
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