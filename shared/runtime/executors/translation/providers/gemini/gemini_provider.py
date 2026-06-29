from shared.config.settings import settings

from shared.runtime.executors.translation.providers.gemini.gemini_client_factory import (
    GeminiClientFactory,
)
from shared.runtime.executors.translation.providers.gemini.gemini_key_pool import (
    GeminiKeyPool,
)
from shared.runtime.executors.translation.providers.gemini.gemini_api_service import (
    GeminiApiService,
)
from shared.runtime.executors.translation.services.gemini_translate_service import (
    GeminiTranslateService,
)


_key_pool = GeminiKeyPool(
    api_keys=settings.llm.gemini.api_keys,
    cooldown_seconds=settings.llm.gemini.cooldown_seconds,
)

_api_service = GeminiApiService(
    key_pool=_key_pool,
    client_factory=GeminiClientFactory(),
    model=settings.llm.gemini.model,
)

gemini_translate_service = GeminiTranslateService(
    api_service=_api_service,
)