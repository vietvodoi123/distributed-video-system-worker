import asyncio
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

URL = "https://ttks.tw/novel/chapters/fudaozhizu/1620.html"

CSS_TITLE = "h1"
CSS_CONTENT = "div.content p"

OUTPUT = Path("debug_output")
OUTPUT.mkdir(exist_ok=True)


def clean_content(text: str) -> str:
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        await page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        await page.wait_for_timeout(5000)

        html = await page.content()

        OUTPUT.joinpath(
            "page_content.html"
        ).write_text(
            html,
            encoding="utf-8"
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        print("=" * 80)
        print("TITLE")
        print("=" * 80)

        title_node = soup.select_one(
            CSS_TITLE
        )

        if title_node:
            print(title_node.get_text(strip=True))

        print()

        print("=" * 80)
        print("CONTENT")
        print("=" * 80)

        nodes = soup.select(
            CSS_CONTENT
        )

        print("Matched nodes:", len(nodes))

        if not nodes:
            print("NOT FOUND")
            return

        node = nodes[0]

        text = clean_content(
            node.get_text(
                separator="\n"
            )
        )

        OUTPUT.joinpath(
            "content.txt"
        ).write_text(
            text,
            encoding="utf-8"
        )

        print("Length:", len(text))
        print()
        print(text[:500])

        print()
        print("=" * 80)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())