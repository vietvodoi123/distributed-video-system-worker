import asyncio

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from apps.api.db.session import (
    AsyncSessionLocal,
)

from apps.api.models.story_source import (
    StorySource
)

from apps.api.models.chapter import (
    Chapter
)

from apps.api.models.website import (
    Website
)

from shared.discovery.services.discovery_service import (
    DiscoveryService
)


async def main():

    async with AsyncSessionLocal() as db:

        # =========================
        # GET STORY SOURCE
        # =========================

        result = await db.execute(

            select(StorySource)

            .join(
                Website,
                StorySource.website_id == Website.id
            )

            .options(
                joinedload(
                    StorySource.website
                ),
                joinedload(
                    StorySource.story
                )
            )

            .where(
                StorySource.is_active == True,
                Website.code == "shuhaige"
            )
        )

        story_source = (
            result.scalars().first()
        )

        if not story_source:

            print(
                "No story source found"
            )

            return

        print("=" * 50)
        print(
            f"Story: "
            f"{story_source.story.original_title}"
        )

        print(
            f"Source: "
            f"{story_source.source_url}"
        )

        # =========================
        # BEFORE COUNT
        # =========================

        before_result = await db.execute(

            select(Chapter)

            .where(
                Chapter.story_id
                == story_source.story_id,

                Chapter.story_source_id
                == story_source.id
            )
        )

        before_chapters = (
            before_result.scalars().all()
        )

        before_count = len(
            before_chapters
        )

        print(
            f"Before sync: "
            f"{before_count} chapters"
        )

        # =========================
        # RUN DISCOVERY
        # =========================

        service = DiscoveryService(
            db
        )

        result = (
            await service.discover_chapters(
                story=story_source.story,
                story_source=story_source,
                website=story_source.website
            )
        )

        print("=" * 50)
        print("SYNC RESULT")
        print(result)

        # =========================
        # AFTER COUNT
        # =========================

        after_result = await db.execute(

            select(Chapter)

            .where(
                Chapter.story_id
                == story_source.story_id,

                Chapter.story_source_id
                == story_source.id
            )
        )

        after_chapters = (
            after_result.scalars().all()
        )

        after_count = len(
            after_chapters
        )

        print("=" * 50)
        print(
            f"After sync: "
            f"{after_count} chapters"
        )

        print(
            f"New chapters inserted: "
            f"{after_count - before_count}"
        )

        # =========================
        # SHOW LATEST
        # =========================

        latest = sorted(
            after_chapters,
            key=lambda x: x.chapter_number,
            reverse=True
        )[:10]

        print("=" * 50)
        print("LATEST CHAPTERS")

        for chapter in latest:

            print(
                f"Chapter "
                f"{chapter.chapter_number}"
            )


if __name__ == "__main__":
    asyncio.run(main())