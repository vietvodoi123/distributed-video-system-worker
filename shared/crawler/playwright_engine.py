import asyncio
from typing import Any

from playwright.async_api import (
    TimeoutError,
    async_playwright,
)

from shared.crawler.base_engine import (
    BaseCrawlerEngine,
)


class PlaywrightCrawlerEngine(
    BaseCrawlerEngine
):

    DEFAULT_TIMEOUT = 30000
    MIN_CONTENT_LENGTH = 200

    async def get_html(
        self,
        url: str,
        **kwargs,
    ) -> str:

        css_content = kwargs.get("css_content")

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=False,
            )

            page = await browser.new_page()

            try:

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.DEFAULT_TIMEOUT,
                )

                if css_content:

                    await self._wait_content_ready(
                        page,
                        css_content,
                    )

                else:

                    await asyncio.sleep(2)

                return await page.content()

            finally:

                await browser.close()

    async def get_json(
        self,
        url: str,
        **kwargs,
    ) -> dict[str, Any]:

        raise NotImplementedError(
            "Playwright json fetch not supported"
        )

    async def _wait_content_ready(
        self,
        page,
        selector: str,
    ) -> None:

        try:

            locator = page.locator(selector)

            await locator.wait_for(
                state="visible",
                timeout=self.DEFAULT_TIMEOUT,
            )

        except TimeoutError:

            raise RuntimeError(
                f"Content selector not found: {selector}"
            )

        try:

            await page.wait_for_function(
                """
                ({selector, minLength}) => {

                    const node = document.querySelector(selector);

                    if (!node)
                        return false;

                    const text = node.innerText || "";

                    return text.trim().length >= minLength;

                }
                """,
                arg={
                    "selector": selector,
                    "minLength": self.MIN_CONTENT_LENGTH,
                },
                timeout=self.DEFAULT_TIMEOUT,
            )

        except TimeoutError:

            text = await locator.inner_text()

            raise RuntimeError(
                "Content selector exists but never received "
                f"enough text ({len(text.strip())} chars)."
            )