import asyncio
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import (
    TimeoutError,
    async_playwright,
)

from shared.crawler.base_engine import (
    BaseCrawlerEngine,
)


class PlaywrightCrawlerEngine(BaseCrawlerEngine):
    DEFAULT_TIMEOUT = 30000
    MIN_CONTENT_LENGTH = 200

    BAD_CHARSETS = {
        "windows-1252",
        "iso-8859-1",
        "latin1",
        "us-ascii",
    }

    PREFERRED_ENCODINGS = (
        "utf-8",
        "utf-8-sig",
        "gb18030",
        "gbk",
        "big5",
    )

    @staticmethod
    def _is_8book_url(url: str) -> bool:
        """Trả về True nếu URL thuộc website 8book.com."""
        hostname = (urlparse(url).hostname or "").lower()
        return hostname == "8book.com" or hostname.endswith(".8book.com")

    @classmethod
    def _decode_8book_response(cls, body: bytes) -> str:
        """
        8book trả nội dung chương dưới dạng HTML có byte UTF-8.
        Giải mã trực tiếp từ response body để tránh lỗi charset của trình duyệt.
        """
        try:
            return body.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                "Không thể giải mã response của 8book bằng UTF-8."
            ) from exc

    @classmethod
    def _decode_response(cls, body: bytes) -> str:
        """Giải mã response theo danh sách encoding ưu tiên."""
        for encoding in cls.PREFERRED_ENCODINGS:
            try:
                return body.decode(encoding)
            except UnicodeDecodeError:
                continue

        return body.decode("utf-8", errors="replace")

    async def get_html(
        self,
        url: str,
        **kwargs,
    ) -> str:
        css_content = kwargs.get("css_content")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
            )

            page = await browser.new_page()

            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.DEFAULT_TIMEOUT,
                )

                if response is None:
                    raise RuntimeError(f"No response: {url}")

                # 8book: dùng byte response gốc và giải mã UTF-8 trực tiếp.
                # Không dùng page.content() vì trình duyệt có thể đã hiển thị
                # nội dung sai charset; cũng không đợi selector trên DOM lỗi.
                if self._is_8book_url(url):
                    body = await response.body()
                    return self._decode_8book_response(body)

                if css_content:
                    await self._wait_content_ready(
                        page,
                        css_content,
                    )
                else:
                    await asyncio.sleep(2)

                charset = (
                    await page.evaluate("document.characterSet")
                ).lower()

                # Nếu trình duyệt giải mã đúng thì trả HTML từ DOM.
                if charset not in self.BAD_CHARSETS:
                    return await page.content()

                # Browser decode có thể sai -> lấy byte response gốc.
                body = await response.body()
                return self._decode_response(body)

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

                    if (!node) {
                        return false;
                    }

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
