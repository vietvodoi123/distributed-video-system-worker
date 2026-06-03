import asyncio

from sqlalchemy import select

from apps.api.db.session import (
    SessionLocal
)

from apps.api.models.website import Website

from apps.api.models.story_source import (
    StorySource
)

from shared.crawler.engine_factory import (
    EngineFactory
)

from shared.discovery.parsers.parser_factory import (
    ParserFactory
)


async def main():

    db = SessionLocal()

    try:

        story_source = (
            db.query(StorySource)
            .first()
        )

        website = (
            db.query(Website)
            .filter(
                Website.id
                == story_source.website_id
            )
            .first()
        )

        engine = EngineFactory.create(
            website=website,
            story_source=story_source
        )

        parser = ParserFactory.create(
            website
        )

        html = await engine.get_html(
            story_source.source_url
        )

        chapters = (
            await parser.extract_chapters(
                html=html,
                source_url=
                story_source.source_url
            )
        )

        print(
            f"TOTAL: {len(chapters)}"
        )

        for chapter in chapters[:10]:

            print(
                chapter.chapter_number,
                chapter.chapter_title,
                chapter.chapter_url,
            )

    finally:

        db.close()


asyncio.run(main())