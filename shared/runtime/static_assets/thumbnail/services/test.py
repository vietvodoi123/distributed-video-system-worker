from pathlib import Path

from shared.runtime.static_assets.thumbnail.services.compose_thumbnail import (
compose_thumbnail

)


# =========================================
# CONFIG
# =========================================

INPUT_IMAGE = Path(
    r"C:\Users\HLC\PycharmProjects\distributed-video-system\shared\runtime\static_assets\thumbnail\services\raw.png"
)

OUTPUT_IMAGE = Path(
    "thumbnail.jpg"
)

FONT_PATH = (
    r"C:\Users\HLC\PycharmProjects\distributed-video-system\shared\runtime\fonts\Anton-Regular.ttf"
)

TITLE = (
    "Võ Thần Chúa Tể: "
    "Vô thượng võ thần, "
    "chúa tể vạn giới"
)

THUMBNAIL_HOOK = ""

EPISODE = "301"


# =========================================
# MAIN
# =========================================

def main():

    compose_thumbnail(

        input_path=
        INPUT_IMAGE,

        output_path=
        OUTPUT_IMAGE,

        title=
        TITLE,

        thumbnail_hook=
        THUMBNAIL_HOOK,

        episode_text=
        EPISODE,

        font_path=
        FONT_PATH,
    )

    print(
        "[TEST] Thumbnail generated:"
    )

    print(
        OUTPUT_IMAGE.resolve()
    )


if __name__ == "__main__":

    main()