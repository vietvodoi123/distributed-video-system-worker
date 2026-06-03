from pathlib import Path

from PIL import Image


def compress_thumbnail(

    input_path: Path,

    max_size_mb: float = 2.0,

    min_quality: int = 55,
) -> Path:

    input_path = Path(
        input_path
    )

    if not input_path.exists():

        raise FileNotFoundError(
            f"Thumbnail not found: "
            f"{input_path}"
        )

    # =====================================
    # LOAD
    # =====================================

    image = Image.open(
        input_path
    )

    # =====================================
    # RGB
    # =====================================

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    # =====================================
    # JPG OUTPUT
    # =====================================

    output_path = (
        input_path.with_suffix(
            ".jpg"
        )
    )

    # =====================================
    # COMPRESS LOOP
    # =====================================

    quality = 95

    while quality >= min_quality:

        image.save(

            output_path,

            format="JPEG",

            quality=quality,

            optimize=True
        )

        size_mb = (
            output_path
            .stat()
            .st_size
            /
            (1024 * 1024)
        )

        print(
            "[compress_thumbnail] "
            f"quality={quality} "
            f"size={size_mb:.2f}MB"
        )

        if size_mb <= max_size_mb:

            break

        quality -= 5

    # =====================================
    # FINAL CHECK
    # =====================================

    final_size_mb = (
        output_path
        .stat()
        .st_size
        /
        (1024 * 1024)
    )

    print(
        "[compress_thumbnail] "
        f"Final size: "
        f"{final_size_mb:.2f}MB"
    )

    return output_path