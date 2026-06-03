import hashlib
import shutil

from pathlib import Path

from shared.runtime.static_assets.base.base_static_asset_manager import (
    BaseStaticAssetManager
)

from shared.runtime.artifacts.artifact_paths import (
    get_mc_cache_dir
)

from shared.runtime.executors.video.services.create_looped_mc_video_from_path import (
    create_looped_mc_video_from_path
)


class McLoopAssetManager(
    BaseStaticAssetManager
):

    asset_name = "mc_loop"

    # =====================================
    # INIT
    # =====================================

    def __init__(
        self,
        mc_path: str,
        artifact_storage
    ):

        self.mc_path = mc_path

        self.artifact_storage = (
            artifact_storage
        )

    # =====================================
    # CACHE KEY
    # =====================================

    def get_cache_key(
        self
    ) -> str:

        return hashlib.md5(
            self.mc_path.encode("utf-8")
        ).hexdigest()

    # =====================================
    # CACHE DIR
    # =====================================

    def get_cache_dir(
        self
    ) -> Path:

        return (
            get_mc_cache_dir()
            / self.get_cache_key()
        )

    # =====================================
    # LOCAL SOURCE
    # =====================================

    def get_local_source_path(
        self
    ) -> Path:

        return (
            self.get_cache_dir()
            / "source.mp4"
        )

    # =====================================
    # CACHE
    # =====================================

    async def ensure_cache_exists(
        self
    ) -> Path:

        cache_dir = (
            self.get_cache_dir()
        )

        cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        local_source = (
            self.get_local_source_path()
        )

        # =================================
        # CACHE HIT
        # =================================

        if local_source.exists():

            print(
                "[McLoopAssetManager] "
                "Using cached MC source"
            )

            return local_source

        # =================================
        # DOWNLOAD
        # =================================

        print(
            "[McLoopAssetManager] "
            "Downloading MC source..."
        )

        temp_path = await (
            self.artifact_storage
            .get_local_path(
                self.mc_path
            )
        )

        shutil.copy(
            temp_path,
            local_source
        )

        if not local_source.exists():

            raise FileNotFoundError(
                f"Failed to cache MC source: "
                f"{local_source}"
            )

        print(
            "[McLoopAssetManager] "
            f"Cached: "
            f"{local_source}"
        )

        return local_source

    # =====================================
    # CREATE VARIANT
    # =====================================

    async def create_duration_variant(

        self,

        duration: float,

        output_path: Path
    ):

        source_video = await (
            self.ensure_cache_exists()
        )

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        print(
            "[McLoopAssetManager] "
            f"Creating MC loop variant "
            f"({duration:.2f}s)"
        )

        create_looped_mc_video_from_path(

            local_input_path=
            source_video,

            output_path=
            output_path,

            duration=
            duration
        )

        if not output_path.exists():

            raise FileNotFoundError(
                f"Failed to create "
                f"MC loop output: "
                f"{output_path}"
            )

        print(
            "[McLoopAssetManager] "
            f"Generated: "
            f"{output_path}"
        )

        return output_path