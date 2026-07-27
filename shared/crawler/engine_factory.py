from shared.crawler.http_engine import HttpCrawlerEngine
from shared.crawler.playwright_engine import PlaywrightCrawlerEngine
from shared.crawler.scrape_do_engine import ScrapeDoEngine
from shared.crawler.flaresolverr_engine import FlareSolverrEngine


class EngineFactory:

    _ENGINES = {
        "http": HttpCrawlerEngine,
        "bs4": HttpCrawlerEngine,
        "playwright": PlaywrightCrawlerEngine,
        "scrape_do": ScrapeDoEngine,
        "flaresolverr": FlareSolverrEngine,
    }

    @classmethod
    def create(
        cls,
        engine_name: str,
        **kwargs
    ):
        engine_cls = cls._ENGINES.get(engine_name)

        if engine_cls is None:
            raise RuntimeError(
                f"Unsupported crawler engine: {engine_name}"
            )

        return engine_cls(**kwargs)