from abc import ABC
from abc import abstractmethod
from pathlib import Path


class BaseStaticAssetManager(
    ABC
):

    asset_name: str = "unknown"

    # =====================================
    # CACHE
    # =====================================

    @abstractmethod
    def ensure_cache_exists(
        self
    ) -> Path:
        raise NotImplementedError

    # =====================================
    # VARIANT
    # =====================================

    @abstractmethod
    def create_duration_variant(
        self,
        duration: float,
        output_path: Path
    ):
        raise NotImplementedError