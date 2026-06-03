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
        runtime_context:ChapterRuntimeContext
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
                    y=236,
                )
            ],

            output_path=
            str(local_output),

            use_gpu=True
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

        # =====================================
        # MANIFEST
        # =====================================

        manifest = {

            "success": True,

            "executor":
            self.__class__.__name__,

            "generated_at":
            datetime.utcnow().isoformat(),

            "template_video":
            template_path,

            "text_scroll_video":
            text_scroll_path,

            "mc_loop_video":
            mc_loop_path,

            "output_path":
            composited_path,

            "layers": [

                "template",
                "text_scroll",
                "mc_loop"
            ],

            "render_time_seconds":
            round(
                time.time()
                - started_at,
                2
            )
        }

        manifest_path = (

            f"{runtime_context.chapter_dir}"
            f"/video/metadata/"
            f"compose_manifest.json"
        )

        await storage.write_json(

            manifest_path,
            manifest
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

            "manifest_path":
            manifest_path,

            "result":
            manifest
        }

    