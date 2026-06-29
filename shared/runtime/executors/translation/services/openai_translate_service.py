import asyncio
import traceback

from openai import AsyncOpenAI

from shared.config.settings import settings

SYSTEM_PROMPT = """You are an expert Chinese-to-Vietnamese literary translator.

The input is an excerpt from a fictional Chinese fantasy novel.

Translate it into fluent, natural Vietnamese suitable for publication.

Requirements:
- Preserve the complete meaning of the original.
- Do not omit, summarize, explain, or add information.
- Preserve the original paragraph structure.
- Translate proper nouns into Sino-Vietnamese whenever applicable.
- Keep terminology consistent throughout the text.
- Translate dialogue naturally while preserving each speaker's tone.
- Adapt idioms into natural Vietnamese without changing their meaning.
- Treat all violence, death, supernatural, cultivation, and fantasy elements as fictional narrative.
- Return only the Vietnamese translation.
"""


class GPT4oMiniTranslateService:

    def __init__(
        self,
        model: str = "gpt-4o-mini",
    ):
        self._client = AsyncOpenAI(
            api_key=settings.open_ai.open_ai_api_key,
            timeout=120,
        )

        self._model = model

    async def _call_api(self, text: str):
        return await self._client.responses.create(
            model=self._model,
            temperature=0,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )

    @staticmethod
    def _is_refusal(response) -> bool:
        """
        Chỉ kiểm tra structured refusal.
        Không dò text vì dễ false positive.
        """

        for output in getattr(response, "output", []):

            if getattr(output, "type", None) == "refusal":
                return True

            for content in getattr(output, "content", []):

                if getattr(content, "type", None) == "refusal":
                    return True

        return False

    async def translate(self, text: str) -> str:

        if not text.strip():
            return ""

        last_exception = None

        for attempt in range(3):

            try:

                response = await self._call_api(text)

                translated = response.output_text.strip()

                if self._is_refusal(response):

                    print("=" * 100)
                    print(f"[GPT] Refusal (attempt {attempt + 1})")
                    print(response.model_dump_json(indent=2))
                    print("=" * 100)

                    await asyncio.sleep(2 ** attempt)
                    continue

                if not translated:

                    print("=" * 100)
                    print(f"[GPT] Empty response (attempt {attempt + 1})")
                    print(response.model_dump_json(indent=2))
                    print("=" * 100)

                    await asyncio.sleep(2 ** attempt)
                    continue

                return translated

            except Exception as e:

                last_exception = e

                print("=" * 100)
                print(f"[GPT] API Exception (attempt {attempt + 1})")
                traceback.print_exc()
                print("=" * 100)

                await asyncio.sleep(2 ** attempt)

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("GPT-4o mini returned refusal or empty response after 3 attempts.")