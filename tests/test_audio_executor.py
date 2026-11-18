import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from shared.contracts.enums.task_types import AUDIO
from shared.runtime.executors.audio.audio_executor import AudioExecutor


class FakeApiClient:
    def __init__(self, chapter_data=None):
        self.chapter_data = chapter_data or {}

    async def get_chapter_text(self, chapter_id: str):
        return self.chapter_data


class FakeStorage:
    def __init__(self):
        self.saved_files = {}

    async def write_bytes(self, path: str, data: bytes):
        self.saved_files[path] = data


class FakeTTSService:
    def __init__(self):
        self.synthesized_calls = []

    async def synthesize_text_async(self, text: str, output_file: Path, options):
        self.synthesized_calls.append(text)
        return SimpleNamespace(duration=1.5)


def _make_audio_task(payload: dict, chapter_id: str = "chap-1"):
    return SimpleNamespace(
        id="task-audio-1",
        task_type=AUDIO,
        chapter_id=chapter_id,
        payload=payload,
    )


def _make_audio_context(api_client, storage, workspace_dir=None):
    return SimpleNamespace(
        chapter_id="chap-1",
        chapter_source_id=None,
        chapter_number=1,
        api_client=api_client,
        artifact_storage=storage,
        workspace_dir=str(workspace_dir or Path(".")),
        gpu_available=False,
        narration_wav_path="batches/b1/chapters/1/narration.wav",
    )


class AudioExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_prepends_translate_title_to_audio_lines(self):
        tts_service = FakeTTSService()
        executor = AudioExecutor(tts_service=tts_service)

        api_client = FakeApiClient()
        storage = FakeStorage()
        ctx = _make_audio_context(api_client, storage)

        task = _make_audio_task({
            "translated_text": "Linh lực cuộn trào.\nTrưởng lão đứng nghiêm.",
            "translate_title": "Chương 1 Đại hội tông môn",
        })

        with patch("shared.runtime.executors.audio.audio_executor.concat_wav_files", new=AsyncMock()):
            with patch("shared.runtime.executors.audio.audio_executor.asyncio.to_thread", new=AsyncMock(return_value=b"RIFFdummy")):
                result = await executor.execute(task, ctx)

        self.assertEqual(len(tts_service.synthesized_calls), 3)
        self.assertEqual(tts_service.synthesized_calls[0], "Chương 1 Đại hội tông môn")
        self.assertEqual(tts_service.synthesized_calls[1], "Linh lực cuộn trào.")
        self.assertEqual(tts_service.synthesized_calls[2], "Trưởng lão đứng nghiêm.")

        self.assertEqual(result["output_path"], "batches/b1/chapters/1/narration.wav")
        self.assertEqual(len(result["segments"]), 3)
        self.assertEqual(result["segments"][0]["line_text"], "Chương 1 Đại hội tông môn")
        self.assertEqual(result["segments"][0]["line_index"], 0)
        self.assertEqual(storage.saved_files["batches/b1/chapters/1/narration.wav"], b"RIFFdummy")

    async def test_fallback_translated_title_key(self):
        tts_service = FakeTTSService()
        executor = AudioExecutor(tts_service=tts_service)

        api_client = FakeApiClient()
        storage = FakeStorage()
        ctx = _make_audio_context(api_client, storage)

        task = _make_audio_task({
            "translated_text": "Nội dung câu chuyện.",
            "translated_title": "Tiêu đề từ translated_title",
        })

        with patch("shared.runtime.executors.audio.audio_executor.concat_wav_files", new=AsyncMock()):
            with patch("shared.runtime.executors.audio.audio_executor.asyncio.to_thread", new=AsyncMock(return_value=b"RIFFdummy")):
                result = await executor.execute(task, ctx)

        self.assertEqual(tts_service.synthesized_calls[0], "Tiêu đề từ translated_title")
        self.assertEqual(tts_service.synthesized_calls[1], "Nội dung câu chuyện.")

    async def test_does_not_duplicate_title_if_already_first_line(self):
        tts_service = FakeTTSService()
        executor = AudioExecutor(tts_service=tts_service)

        api_client = FakeApiClient()
        storage = FakeStorage()
        ctx = _make_audio_context(api_client, storage)

        task = _make_audio_task({
            "translated_text": "Chương 1 Mở đầu\nNội dung câu chuyện.",
            "translate_title": "Chương 1 Mở đầu",
        })

        with patch("shared.runtime.executors.audio.audio_executor.concat_wav_files", new=AsyncMock()):
            with patch("shared.runtime.executors.audio.audio_executor.asyncio.to_thread", new=AsyncMock(return_value=b"RIFFdummy")):
                await executor.execute(task, ctx)

        self.assertEqual(len(tts_service.synthesized_calls), 2)
        self.assertEqual(tts_service.synthesized_calls[0], "Chương 1 Mở đầu")


if __name__ == "__main__":
    unittest.main()
