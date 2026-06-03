from typing import Any

from playwright.async_api import async_playwright

from shared.crawler.base_engine import (
    BaseCrawlerEngine
)


class PlaywrightCrawlerEngine(
    BaseCrawlerEngine
):

    async def get_html(
        self,
        url: str,
        **kwargs
    ) -> str:

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=False
            )

            page = await browser.new_page()

            response = await page.goto(url)

            raw_bytes = await response.body()

            html = raw_bytes.decode(
                "utf-8",
                errors="ignore"
            )

            await browser.close()

            return html

    async def get_json(
        self,
        url: str,
        **kwargs
    ) -> dict[str, Any]:

        raise NotImplementedError(
            "Playwright json fetch not supported"
        )