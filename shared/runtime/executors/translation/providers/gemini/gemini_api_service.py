import asyncio
import logging

from google.genai import types

from shared.runtime.executors.translation.models.gemini_request import (
    GeminiRequest,
)
from shared.runtime.executors.translation.models.gemini_response import (
    GeminiResponse,
)
from shared.runtime.executors.translation.providers.gemini.gemini_client_factory import (
    GeminiClientFactory,
)
from shared.runtime.executors.translation.providers.gemini.gemini_exception_mapper import (
    GeminiExceptionMapper,
)
from shared.runtime.executors.translation.providers.gemini.gemini_key_pool import (
    GeminiKeyPool,
)

logger = logging.getLogger(__name__)


class GeminiApiService:

    def __init__(
        self,
        *,
        key_pool: GeminiKeyPool,
        client_factory: GeminiClientFactory,
        model: str,
    ):
        self._key_pool = key_pool
        self._client_factory = client_factory
        self._model = model

    async def generate(
        self,
        request: GeminiRequest,
    ) -> GeminiResponse:

        while True:

            await self._key_pool.enter_request()

            key = None

            try:

                key = await self._key_pool.acquire()

                client = self._client_factory.create(
                    key.api_key,
                )

                config = types.GenerateContentConfig(
                    temperature=request.temperature,
                    system_instruction=request.system_prompt,
                    max_output_tokens=request.max_output_tokens,
                    response_mime_type=request.response_mime_type,
                )

                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=self._model,
                    contents=request.prompt,
                    config=config,
                )

                if response.text is None:
                    logger.error("=" * 100)
                    logger.error("Gemini returned text=None")
                    logger.error("finish_reason=%s",
                                 response.candidates[0].finish_reason
                                 if response.candidates else None)

                    logger.error("response=%r", response)

                    if response.candidates:
                        logger.error("candidate=%r", response.candidates[0])

                    raise RuntimeError("Gemini returned empty text.")

                await self._key_pool.report_success(
                    key,
                )

                usage = getattr(
                    response,
                    "usage_metadata",
                    None,
                )

                return GeminiResponse(
                    text=response.text,
                    finish_reason=(
                        str(response.candidates[0].finish_reason)
                        if response.candidates
                        else None
                    ),
                    prompt_token_count=getattr(
                        usage,
                        "prompt_token_count",
                        None,
                    ),
                    candidates_token_count=getattr(
                        usage,
                        "candidates_token_count",
                        None,
                    ),
                    total_token_count=getattr(
                        usage,
                        "total_token_count",
                        None,
                    ),
                )

            except Exception as ex:

                if key is None:
                    raise

                if GeminiExceptionMapper.is_permission_error(ex):

                    logger.error(
                        "[GeminiApiService] %s PERMISSION ERROR: %s",
                        key.display_name,
                        ex,
                    )

                    await self._key_pool.disable(
                        key,
                    )

                    continue

                if GeminiExceptionMapper.is_quota_error(ex):

                    logger.warning(
                        "[GeminiApiService] %s QUOTA ERROR: %s",
                        key.display_name,
                        ex,
                    )

                    await self._key_pool.report_quota_error(
                        key,
                    )

                    continue

                if GeminiExceptionMapper.is_network_error(ex):

                    logger.warning(
                        "[GeminiApiService] %s NETWORK ERROR: %s",
                        key.display_name,
                        ex,
                    )

                    await self._key_pool.report_error(
                        key,
                    )

                    continue

                logger.exception(
                    "[GeminiApiService] %s UNKNOWN ERROR",
                    key.display_name,
                )

                await self._key_pool.release(
                    key,
                )

                raise

            finally:

                self._key_pool.leave_request()