from abc import ABC, abstractmethod
from pathlib import Path


class BaseRenderCache(ABC):

    cache_namespace: str = "default"

    @abstractmethod
    def build_cache_key(
        self,
        *args,
        **kwargs
    ) -> str:
        pass

    @abstractmethod
    async def ensure_cache_exists(
        self,
        *args,
        **kwargs
    ) -> Path:
        pass

    @abstractmethod
    async def create_variant(
        self,
        *,
        duration: float,
        output_path: Path,
        **kwargs
    ):
        pass