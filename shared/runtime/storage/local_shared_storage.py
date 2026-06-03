import json

from pathlib import Path

from shared.runtime.storage.base_artifact_storage import (
    BaseArtifactStorage
)


class LocalSharedStorage(
    BaseArtifactStorage
):

    def __init__(
        self,
        root_dir: str = "storage"
    ):

        project_root = (
            Path(__file__)
            .resolve()
            .parents[3]
        )

        self.root_dir = (
            project_root / root_dir
        )

        self.root_dir.mkdir(
            parents=True,
            exist_ok=True
        )
        print(
            "[LocalSharedStorage]",
            self.root_dir
        )

    def _resolve_path(
        self,
        path: str
    ) -> Path:

        return self.root_dir / path

    async def exists(
        self,
        path: str
    ) -> bool:

        full_path = (
            self._resolve_path(path)
        )

        return full_path.exists()

    async def ensure_dir(
        self,
        path: str
    ):

        full_path = (
            self._resolve_path(path)
        )

        full_path.mkdir(
            parents=True,
            exist_ok=True
        )

    async def delete(
        self,
        path: str
    ):

        full_path = (
            self._resolve_path(path)
        )

        if full_path.exists():
            full_path.unlink()

    # =====================================
    # TEXT
    # =====================================

    async def read_text(
        self,
        path: str
    ) -> str:

        full_path = (
            self._resolve_path(path)
        )

        return full_path.read_text(
            encoding="utf-8"
        )

    async def write_text(
        self,
        path: str,
        content: str
    ):

        full_path = (
            self._resolve_path(path)
        )

        full_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        full_path.write_text(
            content,
            encoding="utf-8"
        )

    # =====================================
    # BYTES
    # =====================================

    async def read_bytes(
        self,
        path: str
    ) -> bytes:

        full_path = (
            self._resolve_path(path)
        )

        return full_path.read_bytes()

    async def write_bytes(
        self,
        path: str,
        content: bytes
    ):

        full_path = (
            self._resolve_path(path)
        )

        full_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        full_path.write_bytes(content)

    # =====================================
    # JSON
    # =====================================

    async def read_json(
        self,
        path: str
    ) -> dict:

        text = await self.read_text(path)

        return json.loads(text)

    async def write_json(
        self,
        path: str,
        content: dict
    ):

        text = json.dumps(
            content,
            ensure_ascii=False,
            indent=2
        )

        await self.write_text(
            path,
            text
        )

    # =====================================
    # LOCAL ACCESS
    # =====================================

    async def get_local_path(
        self,
        path: str
    ) -> str:

        full_path = (
            self._resolve_path(path)
        )

        full_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        return str(full_path)