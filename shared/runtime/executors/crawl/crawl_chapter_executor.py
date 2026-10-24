import asyncio
import random
import requests

from shared.crawler.resolvers.chapter_resolver import (
    ChapterResolver
)

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)


from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)

from shared.crawler.engine_factory import EngineFactory
from shared.text.cleaners.cn_cleaner import clean_cn_content
from shared.text.cleaners.cn_validator import (
    validate_raw_text,
    validate_cleaned_chapter,
)
class CrawlChapterExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):
        payload = task.payload or {}

        source_url = payload.get(
            "source_url"
        )

        if not source_url:
            raise ValueError(
                "Missing source_url"
            )


        crawler_config = payload.get(
            "crawler_config",
            {}
        )

        css_title = crawler_config.get(
            "css_title"
        )

        css_content = crawler_config.get(
            "css_content"
        )

        css_next = crawler_config.get(
            "css_next"
        )


        engine_name = payload.get(
            "engine",
            "http"
        )

        # Giả lập hành vi người dùng
        delay = random.uniform(1.5, 4.0)
        await asyncio.sleep(delay)

        # =========================
        # HTTP JSON
        # =========================

        if engine_name == "http":

            resp = requests.get(
                source_url,
                timeout=(10, 20)
            )

            resp.raise_for_status()

            data = resp.json()


            title = (
                data.get(
                    "chaptername",
                    ""
                )
                .replace(
                    "\xa0",
                    " "
                )
                .strip()
            )


            content = (
                data.get(
                    "txt",
                    ""
                )
                .replace(
                    "\xa0",
                    " "
                )
                .strip()
            )


        else:

            resolver = ChapterResolver(

                engine=EngineFactory.create(
                    engine_name
                )
            )

            chapter_data = await resolver.get_chapter(

                source_url,

                css_title=css_title,

                css_content=css_content,

                css_next=css_next
            )

            if not chapter_data:
                raise ValueError(
                    "Resolve chapter failed"
                )

            title = (
                chapter_data.get(
                    "title",
                    ""
                ).strip()
            )

            content = (
                chapter_data.get(
                    "content",
                    ""
                ).strip()
            )


        # =========================
        # CLEAN & VALIDATE TEXT
        # =========================

        raw_text = (
            f"{title}\n\n{content}"
        ).strip()

        if not raw_text:
            raise ValueError(
                "Chapter empty"
            )

        # Validate raw text (encoding / binary / replacement characters)
        validate_raw_text(
            raw_text
        )

        cleaned_content = clean_cn_content(
            content
        )

        cleaned_text = (
            f"{title}\n\n{cleaned_content}"
        ).strip()

        # Validate cleaned text (Chinese character count & ratio)
        validate_cleaned_chapter(
            cleaned_text
        )

        # =========================
        # SAVE TO CONTROL PLANE
        # =========================

        api = (
            runtime_context
            .api_client
        )

        await api.update_chapter_text(
            chapter_id=
            runtime_context.chapter_id,
            data={
                "raw_text":
                raw_text,
                "cleaned_text":
                cleaned_text,
                "original_title":
                title
            }
        )


        print(
            "[CrawlChapterExecutor]",
            "saved chapter",
            runtime_context.chapter_number
        )


        return {

            "result": {

                "chapter_id":
                runtime_context.chapter_id,

                "title":
                title,

                "content_length":
                len(raw_text),

                "metrics": {

                    "output_length":
                    len(raw_text)
                }
            }
        }