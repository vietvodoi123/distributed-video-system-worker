import requests

from datetime import datetime

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

        crawler_config = (
            payload.get(
                "crawler_config",
                {}
            )
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

        if not source_url:

            raise ValueError(
                "Missing source_url"
            )

        engine_name = payload.get(
            "engine",
            "http"
        )

        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # HTTP API JSON
        # =====================================

        if engine_name == "http":


            print(
                "[CrawlChapterExecutor] "
                f"API request: "
                f"{source_url}"
            )

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

                .replace("\xa0", " ")

                .strip()
            )

            raw_cn_content = (

                data.get(
                    "txt",
                    ""
                )

                .replace("\xa0", " ")

                .strip()
            )

            raw_text = (
                f"{title}\n\n"
                f"{raw_cn_content}"
            ).strip()

            html = ""

        # =====================================
        # PLAYWRIGHT ENGINE
        # =====================================

        elif engine_name == "playwright":

            print(
                "[CrawlChapterExecutor] "
                "engine playwright"
            )

            engine = (
                PlaywrightCrawlerEngine()
            )

            resolver = ChapterResolver(
                engine=engine
            )

            chapter_data = (
                await resolver.get_chapter(
                    source_url,

                    css_title=
                    css_title,

                    css_content=
                    css_content,

                    css_next=
                    css_next
                )
            )

            if not chapter_data:

                raise ValueError(
                    "Failed to resolve chapter"
                )

            title = (
                chapter_data.get(
                    "title",
                    ""
                )
                .strip()
            )

            content = (
                chapter_data.get(
                    "content",
                    ""
                )
                .strip()
            )

            raw_text = (
                f"{title}\n\n"
                f"{content}"
            ).strip()

            html = chapter_data.get(
                "html",
                ""
            )

        # =====================================
        # HTTP HTML ENGINE
        # =====================================

        elif engine_name == "bs4":

            print(
                "[CrawlChapterExecutor] "
                "engine http"
            )

            engine = (
                HttpCrawlerEngine()
            )

            resolver = ChapterResolver(
                engine=engine
            )

            chapter_data = (
                await resolver.get_chapter(
                    source_url,

                    css_title=
                    css_title,

                    css_content=
                    css_content,

                    css_next=
                    css_next
                )
            )

            if not chapter_data:

                raise ValueError(
                    "Failed to resolve chapter"
                )

            title = (
                chapter_data.get(
                    "title",
                    ""
                )
                .strip()
            )

            content = (
                chapter_data.get(
                    "content",
                    ""
                )
                .strip()
            )

            raw_text = (
                f"{title}\n\n"
                f"{content}"
            ).strip()

            html = chapter_data.get(
                "html",
                ""
            )

        # =====================================
        # INVALID ENGINE
        # =====================================

        else:

            raise RuntimeError(
                f"Unsupported engine: "
                f"{engine_name}"
            )

        # =====================================
        # VALIDATE CONTENT
        # =====================================

        if not raw_text:

            raise ValueError(
                "Chapter content is empty"
            )

        # =====================================
        # SAVE RAW TEXT
        # =====================================

        await storage.write_text(

            runtime_context.raw_text_path,

            raw_text
        )

        # =====================================
        # SAVE HTML
        # =====================================

        if html:

            await storage.write_text(

                runtime_context.raw_html_path,

                html
            )

        # =====================================
        # SAVE METADATA
        # =====================================

        metadata = {

            "title":
            title,

            "source_url":
            source_url,

            "engine":
            engine_name,

            "chapter_number":
            runtime_context.chapter_number,

            "crawled_at":
            datetime.utcnow().isoformat(),

            "content_length":
            len(raw_text)
        }

        print(
            "[CrawlChapterExecutor]",
            runtime_context.raw_text_path
        )

        await storage.write_json(

            runtime_context.raw_metadata_path,

            metadata
        )

        # =====================================
        # SAVE MANIFEST
        # =====================================

        manifest = {

            "success":
            True,

            "executor":
            self.__class__.__name__,

            "stage":
            "crawl_chapter",

            "artifacts": {

                "raw_text":
                runtime_context.raw_text_path,

                "raw_html":
                runtime_context.raw_html_path,

                "metadata":
                runtime_context.raw_metadata_path
            }
        }

        await storage.write_json(

            runtime_context.crawl_manifest_path,

            manifest
        )

        print(

            "[CrawlChapterExecutor] "

            f"Chapter "

            f"{runtime_context.chapter_number} "

            f"crawled successfully"
        )

        return {

            "result": {

                "title": title,

                "content_length":
                len(raw_text),

                "metrics": {

                    "output_length":
                    len(raw_text)
                }
            },

            "output_path":
            runtime_context.raw_text_path,

            "manifest_path":
            runtime_context.crawl_manifest_path
        }

