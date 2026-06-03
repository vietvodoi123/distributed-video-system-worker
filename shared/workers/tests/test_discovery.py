import asyncio

from sqlalchemy import select

from sqlalchemy.orm import joinedload

from apps.api.db.session import (
    AsyncSessionLocal,
)

from apps.api.models.story import (
    Story
)

from apps.api.models.story_source import (
    StorySource
)

from apps.api.models.website import (
    Website
)

from shared.discovery.services.discovery_service import (
    DiscoveryService
)


# ==========================================
# DISPATCH
# ==========================================

async def dispatch_story_by_ai_title(
    ai_title: str,
    website_code: str = "ttks"
):

    async with AsyncSessionLocal() as db:

        # ==================================
        # LOAD STORY
        # ==================================

        story = await db.scalar(

            select(Story)

            .where(
                Story.ai_title == ai_title
            )
        )

        if not story:

            raise ValueError(
                f"Story not found: "
                f"{ai_title}"
            )

        # ==================================
        # LOAD STORY SOURCE
        # ==================================

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
                StorySource.story_id == story.id,

                StorySource.is_active == True,

                Website.code == website_code
            )
        )

        story_source = (
            result.scalars().first()
        )

        if not story_source:

            raise ValueError(
                f"No story source found "
                f"for: {ai_title}"
            )

        # ==================================
        # DISCOVERY SERVICE
        # ==================================

        service = DiscoveryService(
            db
        )

        result = await (
            service.discover_chapters(

                story=
                story_source.story,

                story_source=
                story_source,

                website=
                story_source.website
            )
        )

        print(result)

        return result


# ==========================================
# MAIN
# ==========================================

async def main():

    await dispatch_story_by_ai_title(
        ai_title="Xuyên Vào Tu Tiên Giới, Ta Dùng Công Nghệ Cải Tổ Cả Môn Phái!",
        website_code="biquge"
    )


if __name__ == "__main__":

    asyncio.run(main())