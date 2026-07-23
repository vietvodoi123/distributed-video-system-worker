import time

from datetime import datetime
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.executors.video.services.video_layer_composer import (
    VideoLayerComposer,
    OverlayLayer
)
from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)


class ComposeVideoLayersExecutor(
    BaseTaskExecutor
):
    CAPABILITIES = [
        "ffmpeg"
    ]

    async def execute(
            self,
            task,
            runtime_context: ChapterRuntimeContext
    ):
        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        # =====================================
        # ARTIFACT PATHS
        # =====================================

        template_path = (
            task.payload.get(
                "template_video_path"
            )
        )

        text_scroll_path = (
            task.payload.get(
                "text_scroll_video_path"
            )
        )

        mc_loop_path = (
            task.payload.get(
                "mc_loop_video_path"
            )
        )

        required = [

            template_path,
            text_scroll_path,
            mc_loop_path
        ]

        for item in required:

            if not item:
                raise ValueError(
                    "Missing compose input"
                )

        composited_path = (
            runtime_context
            .composited_video_path
        )

        # =====================================
        # MATERIALIZE LOCAL FILES
        # =====================================

        local_template = Path(

            await storage.get_local_path(
                template_path,
                runtime_context.workspace_dir
            )
        )

        local_text_scroll = Path(

            await storage.get_local_path(
                text_scroll_path,
                runtime_context.workspace_dir
            )
        )

        local_mc_loop = Path(

            await storage.get_local_path(
                mc_loop_path,
                runtime_context.workspace_dir
            )
        )
        print("MC:", local_mc_loop)
        print("Exists:", local_mc_loop.exists())
        print("Size:", local_mc_loop.stat().st_size)
        # =====================================
        # VALIDATE FILE EXISTENCE
        # =====================================

        required = [

            template_path,
            text_scroll_path,
            mc_loop_path
        ]

        for item in required:

            if not item:
                raise ValueError(
                    "Missing compose input"
                )

        # =====================================
        # OUTPUT
        # =====================================

        local_output = (

                runtime_context
                .workspace_dir
                / "composited.mp4"
        )

        # =====================================
        # COMPOSER
        # =====================================

        composer = (
            VideoLayerComposer()
        )

        # =====================================
        # COMPOSE
        # =====================================

        composer.compose(

            base_video=
            str(local_template),

            overlays=[

                # ==========================
                # TEXT SCROLL
                # ==========================

                OverlayLayer(

                    path=
                    str(local_text_scroll),

                    x=24,
                    y=590
                ),

                # ==========================
                # MC LOOP
                # ==========================

                OverlayLayer(

                    path=
                    str(local_mc_loop),

                    x=961,
                    y=256,
                )
            ],

            output_path=
            str(local_output),

            use_gpu=False
        )

        # =====================================
        # VALIDATE OUTPUT
        # =====================================

        if not local_output.exists():
            raise FileNotFoundError(
                "Compose render failed"
            )

        if local_output.stat().st_size <= 0:
            raise ValueError(
                "Composited video empty"
            )

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(

            composited_path,

            local_output.read_bytes()
        )

        print(

            "[ComposeVideoLayersExecutor] "
            "Completed"
        )

        # =====================================
        # RESULT
        # =====================================

        return {

            "output_path":
                composited_path,

        }
