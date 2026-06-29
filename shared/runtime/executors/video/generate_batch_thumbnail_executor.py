import time

from datetime import datetime
from shared.config.settings import settings

from shared.runtime.artifacts.artifact_paths import (
    get_project_root
)
from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.static_assets.thumbnail.batch_thumbnail_asset_manager import (
    BatchThumbnailAssetManager
)
from shared.runtime.contexts.batch_runtime_context import (BatchRuntimeContext)


class GenerateBatchThumbnailExecutor(
    BaseTaskExecutor
):

    task_type = (
        "generate_batch_thumbnail"
    )

    # =====================================
    # EXECUTE
    # =====================================

    async def execute(
        self,
        task,
        runtime_context:BatchRuntimeContext
    ):

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )
        font_path = str(
            get_project_root()
            / settings.font.font_path
        )

        # =================================
        # STORY
        # =================================

        batch = (
            task.batch
        )

        if not batch:

            raise ValueError(
                "Task batch missing"
            )

        story = (
            batch.story
        )

        if not story:

            raise ValueError(
                "Batch story missing"
            )

        title = (
            getattr(
                story,
                "ai_title",
                None
            )
            or ""
        ).strip()

        description = (
            getattr(
                story,
                "description",
                None
            )
            or ""
        ).strip()

        thumbnail_hook = (
            getattr(
                story,
                "thumbnail_hook",
                None
            )
            or ""
        ).strip()
        story_id = str(story.id)
        # =================================
        # VALIDATE
        # =================================

        if not title:

            raise ValueError(
                "Story title empty"
            )

        if not description:

            raise ValueError(
                "Story description empty"
            )

        if not thumbnail_hook:

            raise ValueError(
                "Thumbnail hook empty"
            )

        # =================================
        # EPISODE TEXT
        # =================================

        episode_text = (

            getattr(
                batch,
                "batch_name",
                None
            )
        )

        episode_text = str(
            episode_text
        )
        print(
            "[GenerateBatchThumbnailExecutor] "
            f"Generating thumbnail for: "
            f"{title}"
        )

        # =================================
        # ASSET MANAGER
        # =================================

        manager = (
            BatchThumbnailAssetManager(

                title=
                title,

                description=
                description,

                thumbnail_hook=
                thumbnail_hook,

                artifact_storage=
                storage,

                runware_api_key=
                settings.runware.api_key,

                font_path=
                font_path,

                episode_text=
                episode_text,
                story_id=story_id,
                model=
                settings.runware.model,
            )
        )

        # =================================
        # ENSURE CACHE
        # =================================

        local_thumbnail = await (
            manager
            .ensure_cache_exists()
        )

        # =================================
        # VALIDATE OUTPUT
        # =================================

        if not local_thumbnail.exists():

            raise FileNotFoundError(
                "Generated thumbnail missing"
            )

        # =================================
        # READ BYTES
        # =================================

        image_bytes = (
            local_thumbnail.read_bytes()
        )

        # =================================
        # UPLOAD FINAL BATCH THUMBNAIL
        # =================================

        await storage.write_bytes(

            runtime_context
            .thumbnail_path,

            image_bytes
        )

        print(
            "[GenerateBatchThumbnailExecutor] "
            f"Uploaded batch thumbnail: "
            f"{runtime_context.thumbnail_path}"
        )

        # =================================
        # MANIFEST
        # =================================

        duration_seconds = round(
            time.time() - started_at,
            2
        )

        manifest = {

            "success": True,

            "executor": (
                self.__class__.__name__
            ),

            "generated_at": (
                datetime.utcnow()
                .isoformat()
            ),

            "story_title": (
                title
            ),

            "thumbnail_hook": (
                thumbnail_hook
            ),

            "cache_key": (
                manager.get_cache_key()
            ),

            "model": (
                manager.model
            ),

            "output_path": (
                runtime_context
                .thumbnail_path
            ),

            "duration_seconds": (
                duration_seconds
            ),

            "episode_text":
                episode_text,
        }

        manifest_path = (
            f"{runtime_context.batch_output_dir}"
            f"/metadata/"
            f"thumbnail_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
        )

        print(
            "[GenerateBatchThumbnailExecutor] "
            "Completed"
        )

        # =================================
        # RESULT
        # =================================

        return {

            "output_path": (
                runtime_context
                .thumbnail_path
            ),

            "manifest_path": (
                manifest_path
            ),

            "result": manifest
        }
