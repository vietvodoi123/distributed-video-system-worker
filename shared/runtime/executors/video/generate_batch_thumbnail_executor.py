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
            runtime_context: BatchRuntimeContext
    ):

        storage = (
            runtime_context
            .artifact_storage
        )
        font_path = str(
            get_project_root()
            / settings.font.font_path
        )

        # =================================
        # STORY METADATA
        # =================================

        payload = (
                task.payload
                or {}
        )

        title = (
            payload.get(
                "title"
            )
        ).strip()

        description = (
            payload.get(
                "description"
            )
        ).strip()

        thumbnail_hook = (
            payload.get(
                "thumbnail_hook"
            )
        ).strip()

        story_id = (
            payload[
                "story_id"
            ]
        )
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

        episode_text = str(

            payload.get(
                "num_eps",
                ""
            )
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
            )
        }
