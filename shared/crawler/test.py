
import asyncio

from shared.crawler.flaresolverr_engine import FlareSolverrEngine


async def main():
    engine = FlareSolverrEngine()

    html = await engine.get_html(
        "https://8book.com/novelbooks/450013/"
    )

    print(html)


if __name__ == "__main__":
    asyncio.run(main())
