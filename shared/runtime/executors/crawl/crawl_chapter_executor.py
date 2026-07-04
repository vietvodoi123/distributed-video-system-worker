import requests

from shared.crawler.resolvers.chapter_resolver import (
    ChapterResolver
)

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.crawler.http_engine import (
    HttpCrawlerEngine
)

from shared.crawler.playwright_engine import (
    PlaywrightCrawlerEngine
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
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


        # =========================
        # PLAYWRIGHT
        # =========================

        elif engine_name == "playwright":


            resolver = ChapterResolver(
                engine=PlaywrightCrawlerEngine()
            )


            chapter_data = (
                await resolver.get_chapter(

                    source_url,

                    css_title=css_title,

                    css_content=css_content,

                    css_next=css_next
                )
            )


            if not chapter_data:

                raise ValueError(
                    "Resolve chapter failed"
                )


            title = (
                chapter_data
                .get(
                    "title",
                    ""
                )
                .strip()
            )


            content = (
                chapter_data
                .get(
                    "content",
                    ""
                )
                .strip()
            )


        # =========================
        # BS4
        # =========================

        elif engine_name == "bs4":


            resolver = ChapterResolver(
                engine=HttpCrawlerEngine()
            )


            chapter_data = (
                await resolver.get_chapter(

                    source_url,

                    css_title=css_title,

                    css_content=css_content,

                    css_next=css_next
                )
            )


            if not chapter_data:

                raise ValueError(
                    "Resolve chapter failed"
                )


            title = (
                chapter_data
                .get(
                    "title",
                    ""
                )
                .strip()
            )


            content = (
                chapter_data
                .get(
                    "content",
                    ""
                )
                .strip()
            )


        else:

            raise RuntimeError(
                f"Unsupported engine {engine_name}"
            )


        # =========================
        # BUILD RAW TEXT
        # =========================

        raw_text = (
            f"{title}\n\n{content}"
        ).strip()


        if not raw_text:

            raise ValueError(
                "Chapter empty"
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