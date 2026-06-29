from pathlib import Path

from shared.runtime.executors.translation.models.gemini_request import (
    GeminiRequest,
)
from shared.runtime.executors.translation.models.post_process_result import (
    PostProcessAction,
)
from shared.runtime.executors.translation.providers.gemini.gemini_api_service import (
    GeminiApiService,
)
from shared.runtime.executors.translation.utils.translation_post_processor import (
    TranslationPostProcessor,
)


class GeminiTranslateService:

    def __init__(
        self,
        api_service: GeminiApiService,
        max_retry: int = 3,
    ):
        self._api_service = api_service
        self._max_retry = max_retry

        self._post_processor = TranslationPostProcessor()

        self._prompt_template = (
            Path(__file__).parent.parent
            / "prompts"
            / "translate_prompt.txt"
        ).read_text(
            encoding="utf-8",
        )

    async def translate(
        self,
        text: str,
    ) -> str:

        prompt = self._prompt_template.replace(
            "{{TEXT}}",
            text,
        )

        request = GeminiRequest(
            prompt=prompt,
            temperature=0.0,
        )

        last_reason = None

        for _ in range(self._max_retry):

            response = await self._api_service.generate(
                request,
            )

            result = self._post_processor.process(
                source_text=text,
                translated_text=response.text,
            )

            if result.action == PostProcessAction.ACCEPT:
                return result.text

            last_reason = result.reason

        raise RuntimeError(
            f"Translation validation failed: {last_reason}"
        )