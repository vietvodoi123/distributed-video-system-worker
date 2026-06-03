import asyncio

from sqlalchemy import select

from sqlalchemy.orm import joinedload

from apps.api.db.session import (
    AsyncSessionLocal
)

from apps.api.models.story import (
    Story
)

from apps.api.models.story_source import (
    StorySource
)

from apps.api.models.batch import (
    Batch
)

from apps.api.models.batch_chapter import (
    BatchChapter
)

from apps.api.models.task import (
    Task
)

from apps.api.models.website import (
    Website
)

from shared.orchestration.services.batch_service import (
    BatchService
)


# ==========================================
# CREATE BATCH
# ==========================================

async def create_story_batch(

    ai_title: str,

    website_code: str,

    start_chapter: int,

    end_chapter: int,

    batch_name: str
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

            .options(

                joinedload(
                    StorySource.story
                ),

                joinedload(
                    StorySource.website
                )
            )

            .join(
                StorySource.website
            )

            .where(

                StorySource.story_id
                == story.id,

                Website.code
                == website_code,

                StorySource.is_active
                == True
            )
        )

        story_source = (
            result.scalars().first()
        )

        if not story_source:

            raise ValueError(
                f"No story source found "
                f"for website: "
                f"{website_code}"
            )

        website = (
            story_source.website
        )

        print("=" * 50)

        print(
            f"Story: "
            f"{story.ai_title}"
        )

        print(
            f"Website: "
            f"{website.code}"
        )

        print(
            f"Chapters: "
            f"{start_chapter}"
            f" -> "
            f"{end_chapter}"
        )

        # ==================================
        # CREATE BATCH
        # ==================================

        service = BatchService(
            db
        )

        batch = await service.create_batch(

            story_id=
            story.id,

            story_source_id=
            story_source.id,

            start_chapter=
            start_chapter,

            end_chapter=
            end_chapter,

            batch_name=
            batch_name,

            engine=
            website.render_engine
        )

        print("=" * 50)

        print(
            f"Batch created: "
            f"{batch.batch_name}"
        )

        print(
            f"Batch ID: "
            f"{batch.id}"
        )

        # ==================================
        # CHECK TASKS
        # ==================================

        result = await db.execute(

            select(Task)

            .where(
                Task.batch_id
                == batch.id
            )
        )

        tasks = (
            result.scalars().all()
        )

        print(
            f"Total tasks: "
            f"{len(tasks)}"
        )

        return batch


# ==========================================
# CREATE MULTIPLE BATCHES
# ==========================================

async def create_multiple_batches():

    jobs = [

        # {
        #     "ai_title": "Phế Vật Ngũ Linh Căn, Ta Có Không Gian Linh Dược Nghịch Thiên!",
        #
        #     "website_code":"ttks",
        #
        #     "start_chapter":1200,
        #
        #     "end_chapter":1202,
        #
        #     "batch_name":"66"
        # },

        # {
        #     "ai_title": "Ta Có Thiên Phú Vô Địch, Một Lòng Chỉ Nghĩ Sống Tạm",
        #
        #     "website_code": "ttks",
        #
        #     "start_chapter": 1395,
        #
        #     "end_chapter": 1399,
        #
        #     "batch_name": "32"
        # },

        # {
        #     "ai_title": "Gia Nhập Tông Môn Miễn Phí… Ai Ngờ Lại Là Ma Giáo?, Bắt Lấy Tên Ma Tu Kia!",
        #
        #     "website_code": "8book",
        #
        #     "start_chapter": 1450,
        #
        #     "end_chapter": 1469,
        #
        #     "batch_name": "37"
        # },

        {
            "ai_title": "Tụ Bảo Tiên Bồn Biến 1 Thành 2, Ta Từ Tạp Dịch Trở Thành Cường Giả",

            "website_code": "ttks",

            "start_chapter": 1775,#1782

            "end_chapter": 1777,

            "batch_name": "49"
        },
        # {
        #     "ai_title": "Xuyên Vào Tu Tiên Giới, Ta Dùng Công Nghệ Cải Tổ Cả Môn Phái!",
        #
        #     "website_code": "xyz",
        #
        #     "start_chapter": 2001,
        #
        #     "end_chapter": 2050,
        #
        #     "batch_name": "41"
        # },
        # {
        #     "ai_title": "Nhặt Được Viên Châu Trắng Trong Khe Đá, Ta Từ Phàm Nhân Bước Lên Tiên Lộ!",
        #
        #     "website_code": "shuhaige",
        #
        #     "start_chapter": 301,
        #
        #     "end_chapter": 350,
        #
        #     "batch_name": "7"
        # },
        # {
        #     "ai_title": "Nuôi Gà Để Tu Tiên, Mỗi Lần Linh Thú Chết Ta Lại Mạnh Lên?!",
        #
        #     "website_code": "ttks",
        #
        #     "start_chapter": 1686,
        #
        #     "end_chapter": 1721,
        #
        #     "batch_name": "58"
        # },
        # {
        #     "ai_title": "Nhặt Được Một Cái Hồ Lô, Ta Chỉ Muốn Làm Ruộng, Ai Ngờ Lại Bị Kéo Vào Tu Tiên!",
        #
        #     "website_code": "ttks",
        #
        #     "start_chapter": 1467,
        #
        #     "end_chapter": 1486,
        #
        #     "batch_name": "33"
        # },
        # {
        #     "ai_title": "Tử Tôn Thắp Hương, Đem Ta Cung Cấp Thành Chân Tiên",
        #
        #     "website_code": "ttks",
        #
        #     "start_chapter": 384,
        #
        #     "end_chapter": 410,
        #
        #     "batch_name": "10"
        # },
    ]

    for job in jobs:

        try:

            await create_story_batch(

                ai_title=
                job["ai_title"],

                website_code=
                job["website_code"],

                start_chapter=
                job["start_chapter"],

                end_chapter=
                job["end_chapter"],

                batch_name=
                job["batch_name"]
            )

        except Exception as e:

            print(
                f"FAILED: "
                f"{job['ai_title']} "
                f"-> {str(e)}"
            )


# ==========================================
# MAIN
# ==========================================

async def main():

    await create_multiple_batches()


if __name__ == "__main__":

    asyncio.run(main())