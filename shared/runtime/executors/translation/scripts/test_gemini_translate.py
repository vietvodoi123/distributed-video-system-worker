import asyncio

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


async def main():

    key_pool = GeminiKeyPool(
        api_keys=settings.llm.gemini.api_keys,
        cooldown_seconds=settings.llm.gemini.cooldown_seconds,
    )

    api_service = GeminiApiService(
        key_pool=key_pool,
        client_factory=GeminiClientFactory(),
        model=settings.llm.gemini.model,
        max_retry=settings.llm.gemini.max_retry,
    )

    translator = GeminiTranslateService(
        api_service=api_service,
    )

    text = """
阴天域，幽国地界，枫山脚下。

通往灵宝观的泥路上，一辆马车不疾不徐，五六骑披甲骑士护卫左右。

奢华的车厢里，沉香袅袅。

一老一少，两人对坐，气氛压抑。

老者叫阴寻山，乃是清河县清河侯府的大管家。

少年则是侯府三公子，但仅是妾婢所生的庶子。

他长得眉清目秀，眉宇间有股清贵之气，看上去约十五六岁的样子，就是气色相当不佳。

带着些许稚气的俊脸上，一片病态般苍白，不见半点血色。

“三少爷，灵宝观快到了，往后就要侍奉道君座前，青灯常伴，夫人让老奴问上一句，你心中可有怨气？”

阴寻山身着华袍，面容阴白，眼珠灰灰的，有点瘆人，似笑非笑地看着对面的李青云。

问这句话时，明显带着几分放肆的挑衅与压迫。

“嗯？”
"""

    result = await translator.translate(
        text,
    )

    print("=" * 80)
    print(result)
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())