from shared.contracts.enums.task_types import (
    GENERATE_BATCH_THUMBNAIL,
    GENERATE_YOUTUBE_DESCRIPTION,
    MERGE_BATCH_VIDEO,
)
from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext,
)
from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext,
)


_BATCH_TASK_TYPES = {
    MERGE_BATCH_VIDEO,
    GENERATE_BATCH_THUMBNAIL,
    GENERATE_YOUTUBE_DESCRIPTION,
}


async def create_runtime_context(
    task,
    worker_id,
    workspace_dir,
    artifact_storage,
    api_client=None,
    gpu_available=False,
):
    payload = getattr(task, "payload", None) or {}
    task_type = getattr(task, "task_type", None)

    chapter_id = getattr(task, "chapter_id", None) or payload.get("chapter_id")
    chapter_source_id = getattr(task, "chapter_source_id", None) or payload.get("chapter_source_id")
    chapter_number = (
        task.chapter_number
        if getattr(task, "chapter_number", None) is not None
        else payload.get("chapter_number")
    )
    batch_id = getattr(task, "batch_id", None) or payload.get("batch_id")
    story_id = getattr(task, "story_id", None) or payload.get("story_id")

    is_chapter_task = (
        task_type not in _BATCH_TASK_TYPES
        and (
            chapter_id is not None
            or chapter_source_id is not None
            or chapter_number is not None
            or task_type in ("text", "audio", "video")
        )
    )

    if is_chapter_task:
        context = ChapterRuntimeContext(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
            batch_id=str(batch_id) if batch_id is not None else None,
            chapter_id=str(chapter_id) if chapter_id is not None else None,
            chapter_number=chapter_number,
            chapter_source_id=str(chapter_source_id) if chapter_source_id is not None else None,
            story_id=str(story_id) if story_id is not None else None,
            api_client=api_client,
            gpu_available=gpu_available,
        )
    else:
        context = BatchRuntimeContext(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
            batch_id=str(batch_id) if batch_id is not None else None,
            gpu_available=gpu_available,
        )

    await context.initialize()

    return context
