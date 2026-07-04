from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)

from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext
)


async def create_runtime_context(
    task,
    worker_id,
    workspace_dir,
    artifact_storage,
    api_client=None,
):
    # =====================================
    # CHAPTER TASK
    # =====================================

    if task.chapter is not None:

        context = (
            ChapterRuntimeContext(

                task=task,

                worker_id=worker_id,

                workspace_dir=workspace_dir,

                artifact_storage=artifact_storage,

                batch_id=str(task.batch_id),

                chapter_id=str(task.chapter_id),

                chapter_number=task.chapter_number,

                api_client=api_client
            )
        )

    # =====================================
    # BATCH TASK
    # =====================================

    else:

        context = (
            BatchRuntimeContext(

                task=task,

                worker_id=worker_id,

                workspace_dir=workspace_dir,

                artifact_storage=artifact_storage,

                batch_id=str(task.batch_id),
            )
        )

    await context.initialize()

    return context