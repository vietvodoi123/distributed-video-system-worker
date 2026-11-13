import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from shared.contracts.enums.task_types import TEXT
from shared.contracts.task_dto import TaskDto
from shared.runtime.exceptions import ExecutorNotFoundError
from shared.runtime.executors.registry.register_executors import register_executors
from shared.runtime.executors.registry.task_executor_registry import TaskExecutorRegistry
from shared.runtime.executors.text.text_executor import (
    TextExecutor,
    filter_corrupted_translation_lines,
)
from shared.runtime.executors.translation.services.moxhi_translate_service import (
    MoxhiTranslateService,
)
from shared.runtime.workers.services.worker_api_client import WorkerApiClient


class FakeApiClient:
    def __init__(self):
        self.updates = []

    async def update_chapter_text(self, *, chapter_id: str, data: dict):
        self.updates.append((chapter_id, data))
        return {"ok": True}


class FakeTranslateService:
    def __init__(self, translated_output: str):
        self.translated_output = translated_output
        self.calls = []

    async def translate(self, text: str, text_type: str = "Ancient") -> str:
        self.calls.append(text)
        return self.translated_output


def _make_task(payload: dict, chapter_id: str = "chap-1", chapter_number: int = 1):
    return SimpleNamespace(
        id="task-1",
        task_type=TEXT,
        attempt_id="attempt-123",
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        payload=payload,
    )


def _make_context(api_client: FakeApiClient, chapter_id: str = "chap-1", chapter_number: int = 1):
    return SimpleNamespace(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        api_client=api_client,
    )


class TextExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_crawl_clean_translate_and_result_format(self):
        cn_body = (
            "柳天雄身上恐怖的靈力涌動，逼迫的柳如煙，柳飛龍兩人，齊齊後退到了三米開外。\n"
            "看書首選天天看小說，ttks.tw超給力\n"
            + ("長老們肅然而立，大殿內一片寂靜，掌門真人緩緩開口說道今日之事非同小可。" * 4)
        )
        fake_resp = MagicMock()
        fake_resp.json.return_value = {
            "chaptername": "第一章\xa0宗門大會",
            "txt": cn_body,
        }
        fake_resp.raise_for_status.return_value = None

        api_client = FakeApiClient()
        translate_service = FakeTranslateService(
            "Chương 1 Đại hội tông môn\n"
            "Linh lực khủng bố trên người Liễu Thiên Hùng cuộn trào."
        )
        executor = TextExecutor(translate_service=translate_service)
        task = _make_task(
            {
                "mode": "crawl_and_translate",
                "source_url": "https://example.com/1",
                "render_engine": "http",
                "parser_type": "json",
            }
        )
        ctx = _make_context(api_client)

        with patch("shared.runtime.executors.text.text_executor.asyncio.sleep", new=AsyncMock()):
            with patch(
                "shared.runtime.executors.text.text_executor.requests.get",
                return_value=fake_resp,
            ) as mock_get:
                result = await executor.execute(task, ctx)

        mock_get.assert_called_once_with("https://example.com/1", timeout=(10, 20))
        self.assertEqual(len(translate_service.calls), 1)
        self.assertNotIn("ttks.tw", translate_service.calls[0])

        expected_translated = (
            "Linh lực khủng bố trên người Liễu Thiên Hùng cuộn trào."
        )
        self.assertEqual(result["original_title"], "第一章 宗門大會")
        self.assertEqual(result["translated_title"], "Chương 1 Đại hội tông môn")
        self.assertIn("ttks.tw", result["raw_text"])
        self.assertNotIn("cleaned_text", result)
        self.assertNotIn("final_script", result)
        self.assertNotIn("final_text", result)
        self.assertEqual(result["translated_text"], expected_translated)
        self.assertNotIn(result["translated_title"], result["translated_text"])

    async def test_resolver_crawl_flow_with_html_http_engine(self):
        cn_body = "長老們肅然而立，大殿內一片寂靜，掌門真人緩緩開口說道今日之事非同小可。" * 5
        fake_resolver = MagicMock()
        fake_resolver.get_chapter = AsyncMock(
            return_value={"title": "第二章 秘境", "content": cn_body}
        )

        api_client = FakeApiClient()
        translate_service = FakeTranslateService("Chương 2 Bí cảnh\nCác trưởng lão đứng nghiêm.")
        executor = TextExecutor(translate_service=translate_service)
        task = _make_task(
            {
                "mode": "crawl_and_translate",
                "source_url": "https://example.com/2",
                "render_engine": "http",
                "parser_type": "html",
                "crawler_config": {"css_title": "h1", "css_content": "#content", "css_next": ".next"},
            }
        )
        ctx = _make_context(api_client, chapter_id="chap-2", chapter_number=2)

        with patch("shared.runtime.executors.text.text_executor.asyncio.sleep", new=AsyncMock()):
            with patch(
                "shared.runtime.executors.text.text_executor.EngineFactory.create",
                return_value=MagicMock(),
            ) as mock_engine_create:
                with patch(
                    "shared.runtime.executors.text.text_executor.ChapterResolver",
                    return_value=fake_resolver,
                ):
                    result = await executor.execute(task, ctx)

        mock_engine_create.assert_called_once_with("http")
        fake_resolver.get_chapter.assert_awaited_once_with(
            "https://example.com/2",
            css_title="h1",
            css_content="#content",
            css_next=".next",
        )
        self.assertEqual(result["original_title"], "第二章 秘境")
        self.assertEqual(result["translated_title"], "Chương 2 Bí cảnh")

    async def test_translate_only_mode_uses_payload_text_without_crawling(self):
        api_client = FakeApiClient()
        translate_service = FakeTranslateService("Chương 3\nNội dung đã dịch")
        executor = TextExecutor(translate_service=translate_service)
        task = _make_task(
            {
                "mode": "translate_only",
                "original_title": "第三章",
                "raw_text": "第三章\n\n原文內容。",
                "cleaned_text": "第三章\n\n原文內容。",
            }
        )
        ctx = _make_context(api_client, chapter_id="chap-3", chapter_number=3)

        result = await executor.execute(task, ctx)

        self.assertEqual(result["raw_text"], "第三章\n\n原文內容。")
        self.assertNotIn("cleaned_text", result)
        self.assertNotIn("final_script", result)
        self.assertEqual(result["translated_text"], "Nội dung đã dịch")
        self.assertEqual(result["original_title"], "第三章")
        self.assertEqual(result["translated_title"], "Chương 3")
        self.assertNotIn(result["translated_title"], result["translated_text"])

    async def test_missing_source_url_raises(self):
        executor = TextExecutor(translate_service=FakeTranslateService("unused"))
        with self.assertRaises(ValueError):
            await executor.execute(_make_task({"mode": "crawl_and_translate"}), _make_context(FakeApiClient()))

    async def test_empty_translation_raises_and_does_not_save(self):
        cn_body = "長老們肅然而立，大殿內一片寂靜，掌門真人緩緩開口說道今日之事非同小可。" * 5
        fake_resp = MagicMock()
        fake_resp.json.return_value = {"chaptername": "第一章", "txt": cn_body}
        fake_resp.raise_for_status.return_value = None

        api_client = FakeApiClient()
        executor = TextExecutor(translate_service=FakeTranslateService(""))

        with patch("shared.runtime.executors.text.text_executor.asyncio.sleep", new=AsyncMock()):
            with patch("shared.runtime.executors.text.text_executor.requests.get", return_value=fake_resp):
                with self.assertRaises(ValueError):
                    await executor.execute(
                        _make_task({"source_url": "https://example.com/1"}),
                        _make_context(api_client),
                    )

        self.assertEqual(api_client.updates, [])



    async def test_worker_api_client_complete_and_fail_send_attempt_id(self):
        client = WorkerApiClient()
        client._post = AsyncMock(return_value={"ok": True})

        await client.complete_task(
            worker_id="w1",
            task_id="t1",
            attempt_id="att-1",
            execution_result={"translated_text": "hello"},
        )
        client._post.assert_awaited_with(
            "/workers/complete-task",
            {
                "worker_id": "w1",
                "task_id": "t1",
                "attempt_id": "att-1",
                "result": {"translated_text": "hello"},
            },
        )

        await client.fail_task(
            worker_id="w1",
            task_id="t1",
            attempt_id="att-1",
            error_message="boom",
        )
        client._post.assert_awaited_with(
            "/workers/fail-task",
            {
                "worker_id": "w1",
                "task_id": "t1",
                "attempt_id": "att-1",
                "error_message": "boom",
            },
        )

    async def test_moxhi_translate_service_supports_native_and_legacy_formats(self):
        service = MoxhiTranslateService(base_url="http://localhost:8090")

        native_resp = MagicMock()
        native_resp.raise_for_status.return_value = None
        native_resp.json.return_value = {"translated_text": "  Nội dung mới  "}

        legacy_resp = MagicMock()
        legacy_resp.raise_for_status.return_value = None
        legacy_resp.json.return_value = {"ok": True, "text": "  Nội dung cũ  "}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False
        mock_client.post = AsyncMock(side_effect=[native_resp, legacy_resp])

        with patch(
            "shared.runtime.executors.translation.services.moxhi_translate_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            self.assertEqual(await service.translate("原文"), "Nội dung mới")
            self.assertEqual(await service.translate("原文"), "Nội dung cũ")

    async def test_execute_works_with_batch_runtime_context(self):
        from shared.runtime.contexts.batch_runtime_context import BatchRuntimeContext
        from pathlib import Path

        translate_service = FakeTranslateService("Chương 1\nNội dung")
        executor = TextExecutor(translate_service=translate_service)
        task = _make_task(
            {
                "mode": "translate_only",
                "original_title": "第1章",
                "raw_text": "第1章\n\n原文內容。",
                "cleaned_text": "第1章\n\n原文內容。",
            },
            chapter_id=None,
            chapter_number=None,
        )
        batch_ctx = BatchRuntimeContext(
            task=task,
            worker_id="w1",
            workspace_dir=Path("."),
            artifact_storage=MagicMock(),
            batch_id="None",
        )

        result = await executor.execute(task, batch_ctx)

        self.assertEqual(result["translated_text"], "Nội dung")
        self.assertEqual(result["original_title"], "第1章")
        self.assertEqual(result["translated_title"], "Chương 1")
        self.assertNotIn(result["translated_title"], result["translated_text"])

    async def test_runtime_context_factory_handles_null_chapter_id_across_task_types(self):
        from pathlib import Path
        from shared.runtime.contexts.batch_runtime_context import BatchRuntimeContext
        from shared.runtime.contexts.chapter_runtime_context import ChapterRuntimeContext
        from shared.runtime.contexts.runtime_context_factory import create_runtime_context

        text_task = TaskDto.from_dict({
            "id": "t-text",
            "task_type": "text",
            "chapter_id": None,
            "batch_id": None,
            "story_id": "story-1",
            "chapter_number": 1.0,
            "payload": {"chapter_source_id": "cs-1"},
        })
        ctx_text = await create_runtime_context(
            task=text_task,
            worker_id="w1",
            workspace_dir=Path("."),
            artifact_storage=MagicMock(),
        )
        self.assertIsInstance(ctx_text, ChapterRuntimeContext)
        self.assertIsNone(ctx_text.chapter_id)
        self.assertEqual(ctx_text.chapter_source_id, "cs-1")
        self.assertEqual(ctx_text.chapter_number, 1)

        audio_task = TaskDto.from_dict({
            "id": "t-audio",
            "task_type": "audio",
            "chapter_id": None,
            "batch_id": "batch-1",
            "chapter_number": 2.0,
            "payload": {"chapter_source_id": "cs-2"},
        })
        ctx_audio = await create_runtime_context(
            task=audio_task,
            worker_id="w1",
            workspace_dir=Path("."),
            artifact_storage=MagicMock(),
        )
        self.assertIsInstance(ctx_audio, ChapterRuntimeContext)
        self.assertEqual(
            ctx_audio.narration_wav_path,
            "batches/batch-1/chapters/2/tts/merged/narration.wav",
        )

        video_task = TaskDto.from_dict({
            "id": "t-video",
            "task_type": "video",
            "chapter_id": None,
            "batch_id": "batch-1",
            "chapter_number": 12.5,
            "payload": {"chapter_source_id": "cs-125"},
        })
        ctx_video = await create_runtime_context(
            task=video_task,
            worker_id="w1",
            workspace_dir=Path("."),
            artifact_storage=MagicMock(),
        )
        self.assertIsInstance(ctx_video, ChapterRuntimeContext)
        self.assertEqual(
            ctx_video.final_video_path,
            "batches/batch-1/chapters/12.5/video/final/final.mp4",
        )

        merge_task = TaskDto.from_dict({
            "id": "t-merge",
            "task_type": "merge_batch_videos",
            "chapter_id": None,
            "batch_id": "batch-1",
            "payload": {},
        })
        ctx_merge = await create_runtime_context(
            task=merge_task,
            worker_id="w1",
            workspace_dir=Path("."),
            artifact_storage=MagicMock(),
        )
        self.assertIsInstance(ctx_merge, BatchRuntimeContext)
        self.assertEqual(ctx_merge.final_video_path, "batches/batch-1/final/final.mp4")

    def test_merge_batch_videos_supports_fractional_chapter_numbers(self):
        from shared.runtime.executors.video.merge_batch_videos_executor import (
            MergeBatchVideosExecutor,
        )

        paths = [
            "batches/b1/chapters/150.01/video/final/final.mp4",
            "batches/b1/chapters/150/video/final/final.mp4",
            "batches/b1/chapters/12.5/video/final/final.mp4",
        ]
        sorted_paths = MergeBatchVideosExecutor._sort_video_paths(paths)
        self.assertEqual(
            sorted_paths,
            [
                "batches/b1/chapters/12.5/video/final/final.mp4",
                "batches/b1/chapters/150/video/final/final.mp4",
                "batches/b1/chapters/150.01/video/final/final.mp4",
            ],
        )

    def test_register_executors_registers_text_executor(self):
        TaskExecutorRegistry._executors.clear()
        with patch("shared.runtime.executors.registry.register_executors.TTSService"):
            register_executors(False, "model.onnx", "model.onnx.json")

        self.assertIsInstance(TaskExecutorRegistry.get_executor("text"), TextExecutor)
        with self.assertRaises(ExecutorNotFoundError):
            TaskExecutorRegistry.get_executor("crawl_chapter")
        with self.assertRaises(ExecutorNotFoundError):
            TaskExecutorRegistry.get_executor("translate_text")


if __name__ == "__main__":
    unittest.main()
