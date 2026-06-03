from pathlib import Path

from shared.runtime.runtime_context import (
    RuntimeContext
)

from shared.runtime.storage.local_shared_storage import (
    LocalSharedStorage
)

from shared.runtime.workspace.workspace_manager import (
    WorkspaceManager
)


class FakeExecutor:

    async def execute(
        self,
        task,
        runtime_context: RuntimeContext
    ):

        output_file = (
            runtime_context.workspace_dir
            / "translated.txt"
        )

        output_file.write_text(
            "hello world",
            encoding="utf-8"
        )

        storage_path = (
            f"storage/{task['id']}/translated.txt"
        )

        await runtime_context.artifact_storage.upload_file(
            local_path=output_file,
            remote_path=storage_path
        )

        return storage_path


async def test_runtime_workspace():

    task = {
        "id": "test-task-001"
    }

    workspace_manager = WorkspaceManager()

    workspace_dir = (
        workspace_manager.create_workspace(
            task["id"]
        )
    )

    artifact_storage = (
        LocalSharedStorage()
    )

    runtime_context = RuntimeContext(
        workspace_dir=workspace_dir,
        worker_id="worker-1",
        artifact_storage=artifact_storage
    )

    executor = FakeExecutor()

    uploaded_path = await executor.execute(
        task,
        runtime_context
    )

    uploaded_file = Path(uploaded_path)

    assert uploaded_file.exists()

    workspace_manager.cleanup_workspace(
        workspace_dir
    )

    assert not workspace_dir.exists()

    assert uploaded_file.exists()

    uploaded_file.unlink()