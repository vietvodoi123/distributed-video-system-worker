import asyncio
import random
import re
import requests

from shared.contracts.enums.task_types import TEXT
from shared.crawler.engine_factory import EngineFactory
from shared.crawler.resolvers.chapter_resolver import ChapterResolver
from shared.runtime.contexts.base_runtime_context import BaseRuntimeContext
from shared.runtime.executors.base.base_task_executor import BaseTaskExecutor
from shared.runtime.executors.translation.services.moxhi_translate_service import (
    MoxhiTranslateService,
)
from spam_cleaner import SpamCleaner
from shared.text.cleaners.cn_validator import (
    validate_cleaned_chapter,
    validate_raw_text,
)


_HEX_BYTE_PATTERN = re.compile(r"<0x[0-9a-fA-F]{2}>")
_DOMAIN_LINE_PATTERN = re.compile(
    r"(?i)^[a-z0-9\-_.]+\.(?:com|tw|net|org|cn|cc|xyz|top)$"
)


def filter_corrupted_translation_lines(text: str) -> str:
    """
    Loại bỏ các dòng chứa mã byte rác hoặc domain bị lỗi dịch:
    - Bắt dấu hiệu '><' (hai thẻ dấu ngoặc nhọn đấu đầu nhau như <0xD0><0xB2>)
    - Bắt mã byte hex <0x..>
    - Bắt dòng chỉ chứa domain còn sót lại
    """
    if not text:
        return ""

    clean_lines = []

    for line in text.splitlines():
        line_stripped = line.strip()

        # 1. Bắt signature '><' (hai thẻ byte đụng đầu nhau)
        if "><" in line_stripped:
            continue

        # 2. Bắt mã byte hex lẻ <0x..>
        if _HEX_BYTE_PATTERN.search(line_stripped):
            continue

        # 3. Bắt dòng chỉ là domain rác sót lại
        if _DOMAIN_LINE_PATTERN.match(line_stripped):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


class TextExecutor(BaseTaskExecutor):
    """Executor xử lý task 'text': crawl (nếu cần), clean/validate bằng SpamCleaner, dịch và trả kết quả."""

    task_type = TEXT

    def __init__(
        self,
        translate_service: MoxhiTranslateService | None = None,
        spam_cleaner: SpamCleaner | None = None,
    ):
        self.translate_service = translate_service
        self.cleaner = spam_cleaner or SpamCleaner()

    async def _crawl_chapter(self, payload: dict) -> tuple[str, str]:
        source_url = payload.get("source_url")
        if not source_url:
            raise ValueError("Missing source_url")

        crawler_config = payload.get("crawler_config") or {}
        css_title = crawler_config.get("css_title")
        css_content = crawler_config.get("css_content")
        css_next = crawler_config.get("css_next")
        engine_name = payload.get("engine") or payload.get("render_engine") or "http"
        parser_type = (payload.get("parser_type") or "").lower()

        # Giả lập hành vi người dùng
        await asyncio.sleep(random.uniform(1.5, 4.0))

        use_json_http = parser_type == "json" or (
            engine_name == "http" and not parser_type and not css_content
        )

        if use_json_http:
            resp = await asyncio.to_thread(
                requests.get,
                source_url,
                timeout=(10, 20),
            )
            resp.raise_for_status()
            content_type = (resp.headers.get("content-type") or "").lower()
            if (
                parser_type == "json"
                or "application/json" in content_type
                or resp.text.lstrip().startswith("{")
            ):
                data = resp.json()
                title = data.get("chaptername", "").replace("\xa0", " ").strip()
                content = data.get("txt", "").replace("\xa0", " ").strip()
                return title, content

        resolver = ChapterResolver(engine=EngineFactory.create(engine_name))
        chapter_data = await resolver.get_chapter(
            source_url,
            css_title=css_title,
            css_content=css_content,
            css_next=css_next,
        )
        if not chapter_data:
            raise ValueError("Resolve chapter failed")

        title = chapter_data.get("title", "").strip()
        content = chapter_data.get("content", "").strip()
        return title, content

    async def _prepare_source_text(self, payload: dict) -> tuple[str, str, str]:
        """Trả về (original_title, raw_text, cleaned_text) theo payload.mode."""
        mode = (payload.get("mode") or "").lower()
        existing_cleaned = (payload.get("cleaned_text") or "").strip()
        existing_raw = (payload.get("raw_text") or "").strip()
        payload_title = (payload.get("original_title") or "").strip()

        is_translate_only = mode == "translate_only" or (
            mode != "crawl_and_translate" and bool(existing_cleaned or existing_raw)
        )

        if is_translate_only:
            raw_text = existing_raw or existing_cleaned
            if not raw_text:
                raise ValueError("Missing raw_text/cleaned_text for translate_only mode")

            if existing_cleaned:
                cleaned_text = existing_cleaned
            else:
                validate_raw_text(raw_text)
                cleaned_text = self.cleaner.clean_text(raw_text)

            title = payload_title or _first_non_empty_line(cleaned_text)
            return title, raw_text, cleaned_text

        # Default / mode == "crawl_and_translate"
        crawled_title, content = await self._crawl_chapter(payload)
        title = crawled_title or payload_title

        raw_text = f"{title}\n\n{content}".strip() if title else content.strip()
        if not raw_text:
            raise ValueError("Chapter empty")

        validate_raw_text(raw_text)

        cleaned_content = self.cleaner.clean_text(content)
        cleaned_text = f"{title}\n\n{cleaned_content}".strip() if title else cleaned_content.strip()

        validate_cleaned_chapter(cleaned_text)
        return title, raw_text, cleaned_text

    async def execute(
        self,
        task,
        runtime_context: BaseRuntimeContext,
    ):
        payload = task.payload or {}
        chapter_id = (
            getattr(runtime_context, "chapter_id", None)
            or getattr(task, "chapter_id", None)
            or payload.get("chapter_id")
        )
        chapter_source_id = (
            getattr(runtime_context, "chapter_source_id", None)
            or getattr(task, "chapter_source_id", None)
            or payload.get("chapter_source_id")
        )
        chapter_number = (
            getattr(runtime_context, "chapter_number", None)
            or getattr(task, "chapter_number", None)
            or payload.get("chapter_number")
        )

        # =========================
        # 1. CRAWL / PREPARE TEXT
        # =========================
        original_title, raw_text, text_to_translate = await self._prepare_source_text(payload)

        # =========================
        # 2. TRANSLATE TEXT
        # =========================
        translate_service = self.translate_service or MoxhiTranslateService()
        chapter_translated = await translate_service.translate(text_to_translate)

        if not chapter_translated:
            raise ValueError("Translated text is empty")

        translated_title = _first_non_empty_line(chapter_translated)
        if original_title and not text_to_translate.startswith(original_title):
            translated_title_raw = await translate_service.translate(original_title)
            translated_title = translated_title_raw.strip() or translated_title

        if isinstance(chapter_number, float) and chapter_number.is_integer():
            chapter_number = int(chapter_number)

        chap_label = (
            f"ch.{chapter_number}"
            if chapter_number is not None
            else str(chapter_source_id or chapter_id or getattr(task, "id", "unknown"))[:8]
        )
        short_task_id = str(getattr(task, "id", ""))[:8]
        print(
            f"[TextExecutor] [{chap_label} {short_task_id}] "
            f"raw={len(raw_text)} -> vi={len(chapter_translated)} ({translated_title})"
        )

        return {
            "translated_text": chapter_translated,
            "original_title": original_title,
            "translated_title": translated_title,
            "raw_text": raw_text,
        }
