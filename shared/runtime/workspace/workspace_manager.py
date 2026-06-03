import shutil

from pathlib import Path


class WorkspaceManager:

    def create_workspace(
        self,
        task_id
    ) -> Path:

        workspace_dir = (
            Path("tmp")
            / str(task_id)
        )

        workspace_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        return workspace_dir

    def cleanup_workspace(
        self,
        workspace_dir: Path
    ):

        shutil.rmtree(
            workspace_dir,
            ignore_errors=True
        )