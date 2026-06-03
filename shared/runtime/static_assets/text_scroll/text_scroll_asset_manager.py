from pathlib import Path

from shared.runtime.static_assets.base.base_static_asset_manager import (
    BaseStaticAssetManager
)

from shared.runtime.artifacts.artifact_paths import (

    get_text_scroll_content_path,

    get_text_scroll_master_cache_path,

    get_text_scroll_cache_dir
)

from shared.runtime.executors.video.services.create_scrolling_text_video import (
    create_scrolling_text_video
)

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_safe
)


class TextScrollAssetManager(
    BaseStaticAssetManager
):

    asset_name = "text_scroll"

    MASTER_DURATION_SECONDS = 3600

    # =====================================
    # CACHE
    # =====================================

    def ensure_cache_exists(
        self
    ) -> Path:

        cache_path = (
            get_text_scroll_master_cache_path()
        )

        if cache_path.exists():

            print(
                "[TextScrollAssetManager] "
                "Using cached master render"
            )

            return cache_path

        cache_dir = (
            get_text_scroll_cache_dir()
        )

        cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        content_path = (
            get_text_scroll_content_path()
        )

        if not content_path.exists():

            raise FileNotFoundError(
                f"Missing content file: "
                f"{content_path}"
            )

        text = content_path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:

            raise ValueError(
                "Text scroll content is empty"
            )

        print(
            "[TextScrollAssetManager] "
            "Rendering master cache..."
        )

        create_scrolling_text_video(

            text=text,

            font_size=20,

            speed=100,

            y_position=12,

            resolution=(1232, 50),

            font_color="white",

            output_path=cache_path,

            total_duration=(
                self
                .MASTER_DURATION_SECONDS
            ),

            use_gpu=True
        )

        return cache_path

    # =====================================
    # CREATE VARIANT
    # =====================================

    def create_duration_variant(
        self,
        duration: float,
        output_path: Path
    ):

        master_path = (
            self.ensure_cache_exists()
        )

        cmd = [

            "ffmpeg",
            "-y",

            "-stream_loop",
            "-1",

            "-i",
            str(master_path),

            "-t",
            str(duration),

            "-c",
            "copy",

            str(output_path)
        ]

        run_ffmpeg_safe(cmd)

        return output_path