import asyncio

from shared.crawler.engine_factory import (
    EngineFactory
)

from apps.api.models.website import Website


async def main():

    website = Website(
        render_engine="http",
        timeout=30,
        retry_limit=3,
        crawler_config={
            "headers": {
                "User-Agent":
                "Mozilla/5.0"
            }
        }
    )

    engine = EngineFactory.create(
        website=website
    )

    html = await engine.get_html(
        "https://m.shuhaige.net/259474"
    )

    print(html[:1000])


asyncio.run(main())