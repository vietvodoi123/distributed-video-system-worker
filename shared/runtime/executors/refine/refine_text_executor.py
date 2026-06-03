from datetime import datetime
import time

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.refine.services.ollama_translate_service import (
    OllamaTranslateService
)

from shared.runtime.executors.refine.utils.line_chunker import (
    LineChunker
)

from shared.runtime.executors.refine.utils.name_mapper import (
    NameMapper
)

from shared.runtime.executors.refine.utils.chinese_detector import (
    ChineseDetector
)

from shared.runtime.contexts.chapter_runtime_context import (ChapterRuntimeContext)
class RefineTextExecutor(
    BaseTaskExecutor
):

    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):

        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # INPUT
        # =====================================

        input_path = (
            task.payload.get(
                "input_path"
            )
        )

        if not input_path:

            raise ValueError(
                "Missing translation input path"
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
                "Translation text is empty"
            )

        # =====================================
        # LOAD GLOSSARY
        # =====================================

        mapper = NameMapper(
            "shared/runtime/executors/refine/glossary/global_glossary.json",
            "shared/runtime/executors/refine/glossary/story_glossary.json",
        )

        # =====================================
        # CHUNK
        # =====================================

        chunks = (
            LineChunker
            .chunk_by_lines(
                raw_text,
                max_lines=8
            )
        )

        refiner = (
            OllamaTranslateService(
                model="gemma3:12b"
            )
        )

        refined_chunks = []

        started_at = time.time()

        total_chunks = len(chunks)

        # =====================================
        # REFINE
        # =====================================

        for index, chunk in enumerate(chunks):

            print(
                "[RefineTextExecutor] "
                f"Refining chunk "
                f"{index + 1}/{total_chunks}"
            )

            normalized_chunk = (
                mapper.replace(chunk)
            )

            refined = (
                await refiner.translate(
                    normalized_chunk
                )
            )

            # =================================
            # CLEANUP
            # =================================

            refined = (
                refined
                .replace("。", ".")
                .replace("，", ",")
                .replace("：", ":")
                .replace("！", "!")
                .replace("？", "?")
            )

            # =================================
            # RETRY IF CHINESE DETECTED
            # =================================

            if ChineseDetector.has_chinese(
                refined
            ):

                print(
                    "[RefineTextExecutor] "
                    "Chinese detected. "
                    "Retrying..."
                )

                refined = (
                    await refiner.translate(
                        normalized_chunk
                    )
                )

            refined_chunks.append(
                refined
            )

        # =====================================
        # MERGE
        # =====================================

        final_script = (
            "\n\n".join(
                refined_chunks
            )
        )

        # =====================================
        # OUTPUT
        # =====================================

        output_path = (
            runtime_context
            .final_script_path
        )

        await storage.write_text(
            output_path,
            final_script
        )

        duration = (
            round(
                time.time() - started_at,
                2
            )
        )

        # =====================================
        # MANIFEST
        # =====================================

        manifest = {
            "success": True,
            "executor": (
                self.__class__.__name__
            ),
            "stage": "refine_text",
            "model": (
                refiner.model
            ),
            "chunks": total_chunks,
            "duration_seconds": duration,
            "refined_at": (
                datetime.utcnow()
                .isoformat()
            ),
            "input_path": input_path,
            "output_path": output_path,
        }

        manifest_path = (
            f"{runtime_context.chapter_dir}"
            f"/refine/"
            f"refine_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
        )

        # =====================================
        # UNLOAD MODEL
        # =====================================

        await refiner.unload_model()

        print(
            "[RefineTextExecutor] "
            f"Refine completed "
            f"in {duration}s"
        )

        return {
            "output_path": output_path,
            "manifest_path": manifest_path,
            "result": {
                "chunks": total_chunks,
                "duration_seconds": duration,
                "metrics": {

                    "input_length":
                        len(raw_text),

                    "output_length":
                        len(final_script),

                    "executor_duration":
                        duration
                }
            }
        }

