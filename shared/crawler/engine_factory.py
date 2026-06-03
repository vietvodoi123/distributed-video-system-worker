from shared.crawler.http_engine import (
    HttpCrawlerEngine
)

from shared.crawler.playwright_engine import (
    PlaywrightCrawlerEngine
)


class EngineFactory:

    @staticmethod
    def create(
        engine_name: str = "http",
        **kwargs
    ):

        if engine_name == "playwright":

            return PlaywrightCrawlerEngine(
                **kwargs
            )

        return HttpCrawlerEngine(
            **kwargs
        )