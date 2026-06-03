from abc import ABC
from abc import abstractmethod


class BaseArtifactStorage(ABC):

    @abstractmethod
    async def exists(
        self,
        path: str
    ) -> bool:
        pass

    @abstractmethod
    async def ensure_dir(
        self,
        path: str
    ):
        pass

    @abstractmethod
    async def delete(
        self,
        path: str
    ):
        pass

    # =====================================
    # TEXT
    # =====================================

    @abstractmethod
    async def read_text(
        self,
        path: str
    ) -> str:
        pass

    @abstractmethod
    async def write_text(
        self,
        path: str,
        content: str
    ):
        pass

    # =====================================
    # BYTES
    # =====================================

    @abstractmethod
    async def read_bytes(
        self,
        path: str
    ) -> bytes:
        pass

    @abstractmethod
    async def write_bytes(
        self,
        path: str,
        content: bytes
    ):
        pass

    # =====================================
    # JSON
    # =====================================

    @abstractmethod
    async def read_json(
        self,
        path: str
    ) -> dict:
        pass

    @abstractmethod
    async def write_json(
        self,
        path: str,
        content: dict
    ):
        pass

    # =====================================
    # LOCAL ACCESS
    # =====================================

    @abstractmethod
    async def get_local_path(
            self,
            path: str,
            workspace_dir: str
    ) -> str:
        pass