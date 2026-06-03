import httpx
from typing import Any

from shared.crawler.base_engine import BaseCrawlerEngine


class HttpCrawlerEngine(BaseCrawlerEngine):

    def __init__(
        self,
        website=None,
        story_source=None
    ):
        super().__init__(website, story_source)

        self.timeout = (
            website.timeout
            if website else 30
        )

        self.retry_limit = (
            website.retry_limit
            if website and website.retry_limit
            else 3
        )

        self.headers = {}

        if website:
            self.headers.update(
                website.crawler_config.get(
                    "headers",
                    {}
                )
            )

    async def get_html(
        self,
        url: str,
        **kwargs
    ) -> str:

        for attempt in range(
            1,
            self.retry_limit + 1
        ):

            try:

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    headers=self.headers,
                    follow_redirects=True
                ) as client:

                    response = await client.get(
                        url
                    )

                    response.raise_for_status()

                    return response.text

            except Exception as e:

                if attempt >= self.retry_limit:
                    raise e

        raise RuntimeError(
            f"Failed to fetch html: {url}"
        )

    async def get_json(
        self,
        url: str,
        **kwargs
    ) -> dict[str, Any]:

        for attempt in range(
            1,
            self.retry_limit + 1
        ):

            try:

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    headers=self.headers,
                    follow_redirects=True
                ) as client:

                    response = await client.get(
                        url
                    )

                    response.raise_for_status()

                    return response.json()

            except Exception as e:

                if attempt >= self.retry_limit:
                    raise e

        raise RuntimeError(
            f"Failed to fetch json: {url}"
        )