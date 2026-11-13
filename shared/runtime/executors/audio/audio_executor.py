import asyncio
from pathlib import Path
import time

from shared.config.settings import settings
from shared.runtime.contexts.chapter_runtime_context import ChapterRuntimeContext
from shared.runtime.executors.audio.service.models import TTSOptions
from shared.runtime.executors.audio.service.tts_service import TTSService
from shared.runtime.executors.audio.utils.audio_concat import concat_wav_files
from shared.runtime.executors.base.base_task_executor import BaseTaskExecutor


class AudioExecutor(BaseTaskExecutor):
    """Executor xử lý task 'audio': tổng hợp giọng đọc TTS và ghép thành file narration WAV."""

    def __init__(
        self,
        *,
        tts_service: TTSService,
    ):
        self.tts_service = tts_service

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext,
    ):
        started_at = time.time()
        api = runtime_context.api_client
        storage = runtime_context.artifact_storage
        payload = getattr(task, "payload", {}) or {}

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
        chapter_ref = chapter_source_id or chapter_id or getattr(task, "id", "unknown")

        # =====================================
        # 1. LẤY VĂN BẢN VÀ TIÊU ĐỀ ĐÃ DỊCH
        # =====================================
        translate_text = payload.get("final_script") or payload.get("translated_text")
        translate_title = payload.get("translate_title") or payload.get("translated_title")

        if not translate_text:
            chapter_data = None
            if chapter_id:
                chapter_data = await api.get_chapter_text(chapter_id)
            elif chapter_source_id and hasattr(api, "get_chapter_source_text"):
                chapter_data = await api.get_chapter_source_text(chapter_source_id)

            if not chapter_data:
                raise RuntimeError(
                    f"Cannot load chapter text: chapter={chapter_ref}"
                )

            translate_text = (
                chapter_data.get("final_script")
                or chapter_data.get("translated_text")
            )
            if not translate_title:
                translate_title = (
                    chapter_data.get("translate_title")
                    or chapter_data.get("translated_title")
                )

        if not translate_text:
            raise RuntimeError(
                f"Chapter has no translated_text: chapter={chapter_ref}"
            )

        # =====================================
        # 2. TÁCH DÒNG VÀ CHÈN TIÊU ĐỀ VÀO ĐẦU
        # =====================================
        raw_lines = translate_text.split("\n")
        lines = [line.strip() for line in raw_lines if line.strip()]

        if translate_title and translate_title.strip():
            title_line = translate_title.strip()
            if not lines or lines[0] != title_line:
                lines.insert(0, title_line)

        if not lines:
            raise RuntimeError(
                f"Translated text contains no usable lines: chapter={chapter_ref}"
            )

        title_info = f" (title: '{translate_title}')" if translate_title else ""
        print(
            f"[AudioExecutor] Chapter={chapter_ref} Lines={len(lines)}{title_info}"
        )

        # =====================================
        # 3. CẤU HÌNH TTS OPTIONS
        # =====================================
        speed = payload.get("speed", getattr(settings.tts, "default_speed", 1.0))
        options = TTSOptions(
            speed=speed,
            volume=1.0,
            sentence_silence=0.0,
        )

        # =====================================
        # 4. TỔNG HỢP TTS TỪNG DÒNG (SHARED SEMAPHORE)
        # =====================================
        async def synthesize_line(line_index: int, line_text: str):
            output_file = (
                Path(runtime_context.workspace_dir)
                / f"tts_line_{line_index:04d}.wav"
            )

            result = await self.tts_service.synthesize_text_async(
                text=line_text,
                output_file=output_file,
                options=options,
            )

            return {
                "line_index": line_index,
                "line_text": line_text,
                "output_path": str(output_file),
                "duration": result.duration,
            }

        results = await asyncio.gather(
            *(
                synthesize_line(line_index, line_text)
                for line_index, line_text in enumerate(lines)
            )
        )
        segments = list(results)
        segment_files = [Path(segment["output_path"]) for segment in segments]

        # =====================================
        # 5. GHÉP CÁC FILE WAV THÀNH MERGED.WAV
        # =====================================
        merged_local_path = str(
            Path(runtime_context.workspace_dir) / "merged.wav"
        )

        await concat_wav_files(
            input_files=segment_files,
            output_file=merged_local_path,
            workspace_dir=Path(runtime_context.workspace_dir),
            use_gpu=runtime_context.gpu_available,
            apply_loudnorm=False,
        )

        # =====================================
        # 6. LƯU VÀO STORAGE
        # =====================================
        def read_file_bytes(p: str) -> bytes:
            with open(p, "rb") as f:
                return f.read()

        merged_bytes = await asyncio.to_thread(
            read_file_bytes,
            merged_local_path,
        )

        await storage.write_bytes(
            runtime_context.narration_wav_path,
            merged_bytes,
        )

        # =====================================
        # 7. XÂY DỰNG TIMELINE SEGMENTS
        # =====================================
        result_segments = []
        current_time = 0.0

        for segment in segments:
            segment_duration = round(segment["duration"], 3)
            start_time = round(current_time, 3)
            end_time = round(current_time + segment_duration, 3)

            result_segments.append({
                "line_index": segment["line_index"],
                "line_text": segment["line_text"],
                "start_time": start_time,
                "end_time": end_time,
                "duration": segment_duration,
            })
            current_time = end_time

        duration = round(current_time, 3)
        elapsed = round(time.time() - started_at, 3)

        print(
            f"[AudioExecutor] Generated {len(segments)} segments "
            f"duration={duration}s elapsed={elapsed}s"
        )

        return {
            "output_path": runtime_context.narration_wav_path,
            "duration": duration,
            "segments": result_segments,
        }