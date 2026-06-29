# shared/runtime/executors/translation/refine_text_executor.py

import traceback
import time
from datetime import datetime
from shared.config.settings import settings
from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.translation.providers.gemini.gemini_provider import (
    gemini_translate_service,
)

from shared.runtime.executors.translation.utils.text_spliter import (
    TextSplitter
)

from shared.runtime.executors.translation.utils.chunk_merger import (
    ChunkMerger
)

from shared.runtime.executors.translation.utils.duplicate_remover import (
    DuplicateRemover
)
from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)

class TranslateTextExecutor(
    BaseTaskExecutor
):
    MAX_CHARS = (
        settings.translation.chunk_max_chars
    )

    # RETRY_COUNT = 3

    async def execute(
        self,
        task,
        runtime_context:ChapterRuntimeContext
    ):

        storage = (
            runtime_context
            .artifact_storage
        )

        input_path = (
            task.payload.get(
                "input_path"
            )
        )

        if not input_path:

            raise ValueError(
                "Missing upstream output path"
            )

        if not await storage.exists(
            input_path
        ):

            raise FileNotFoundError(
                f"Input not found: "
                f"{input_path}"
            )

        raw_text = await storage.read_text(
            input_path
        )

        raw_text = raw_text.strip()

        if not raw_text:

            raise ValueError(
                "Input text is empty"
            )

        chunks = (
            TextSplitter
            .split_by_lines(
                raw_text,
                max_chars=self.MAX_CHARS
            )
        )


        translated_chunks = []

        failed_chunks = 0

        started_at = time.time()

        total_chunks = len(chunks)

        for index, chunk in enumerate(chunks):

            chunk_id = index + 1

            print("\n" + "=" * 120)
            print(f"[Translate] Chunk {chunk_id}/{total_chunks}")
            print(f"Length : {len(chunk)} chars")
            print("=" * 120)

            translated = None


            started = time.perf_counter()

            print(
                f"\n[Translate] "
                f"Chunk {chunk_id}/{total_chunks}"
            )

            try:

                print("[Translate] Calling Gemini...")

                translated = await gemini_translate_service.translate(
                    chunk,
                )

                elapsed = time.perf_counter() - started

                print(
                    f"[Translate] SUCCESS "
                    f"({elapsed:.2f}s)"
                )


            except Exception as e:

                elapsed = time.perf_counter() - started

                print("\n" + "!" * 120)
                print(
                    f"[Translate] FAILED "
                    f"Chunk {chunk_id}/{total_chunks}"
                )
                print(f"Elapsed : {elapsed:.2f}s")
                print(f"Type    : {type(e).__name__}")
                print(f"Message : {e}")
                print("-" * 120)

                traceback.print_exc()

                print("!" * 120 + "\n")

            if translated is None:
                failed_chunks += 1

                raise RuntimeError(
                    f"Translation failed at chunk "
                    f"{chunk_id}/{total_chunks}."
                )

            translated_chunks.append(translated)


        merged = (
            ChunkMerger
            .merge_smart(
                translated_chunks
            )
        )

        final_translation = (
            DuplicateRemover
            .clean(merged)
        )

        output_path = (
            runtime_context
            .translation_text_path
        )

        await storage.write_text(
            output_path,
            final_translation
        )

        duration = round(
            time.time() - started_at,
            2
        )

        manifest = {
            "success": True,
            "executor": (
                self.__class__.__name__
            ),
            "translator": "gemini",
            "model": settings.llm.gemini.model,
            "chunks": total_chunks,
            "failed_chunks": failed_chunks,
            "max_chars": self.MAX_CHARS,
            "duration_seconds": duration,
            "translated_at": (
                datetime.utcnow()
                .isoformat()
            ),
            "input_path": input_path,
            "output_path": output_path,
            "input_length": len(raw_text),

            "output_length": len(final_translation),
        }

        manifest_path = (
            f"{runtime_context.chapter_dir}"
            f"/translation/"
            f"translation_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
        )

        print(
            "[TranslateTextExecutor] "
            f"Translation completed "
            f"in {duration}s"
        )

        return {

            "output_path": output_path,

            "manifest_path": manifest_path,

            "result": {

                "chunks": total_chunks,

                "output_length": len(
                    final_translation
                ),

                "duration_seconds": duration,

                "metrics": {

                    "input_length":
                        len(raw_text),

                    "output_length":
                        len(final_translation),

                    "output_segments":
                        total_chunks,

                    "executor_duration":
                        duration
                }
            }
        }

    def get_resource_requirements(
            self,
            task,runtime_context
    ):

        text_length = len(
            task.payload.get(
                "text",
                ""
            )
        )

        chunk_factor = max(
            1,
            text_length / 10000
        )

        return {

            "cpu": 1 * chunk_factor,

            "ram": 1,

            "gpu": 0,

            "network": min(
                10,
                3 + chunk_factor
            ),

            "disk_io": 1
        }