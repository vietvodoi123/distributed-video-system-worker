import subprocess

from pathlib import Path


def create_video_from_concat(

    concat_file: str,

    output_file: str,

    fps: int = 8,

    codec: str = "libx264",

    preset: str = "medium",

    crf: int = 18,
):

    """
    Render MP4 video from FFmpeg concat.txt

    Args:
        concat_file:
            FFmpeg concat demuxer file

        output_file:
            Final output video path

        fps:
            Output FPS

        codec:
            Video codec

        preset:
            FFmpeg preset

        crf:
            Video quality
    """

    concat_file = Path(
        concat_file
    )

    output_file = Path(
        output_file
    )

    # =====================================
    # VALIDATE
    # =====================================

    if not concat_file.exists():

        raise FileNotFoundError(
            f"Concat file not found: "
            f"{concat_file}"
        )

    concat_content = (
        concat_file.read_text(
            encoding="utf-8"
        ).strip()
    )

    if not concat_content:

        raise ValueError(
            "Concat file is empty"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================
    # FFMPEG CMD
    # =====================================

    cmd = [

        "ffmpeg",

        "-y",

        # ================================
        # INPUT
        # ================================

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(
            concat_file.resolve()
        ),

        # ================================
        # VIDEO
        # ================================

        "-vsync",
        "vfr",

        "-pix_fmt",
        "yuv420p",


        "-c:v",
        codec,

        "-preset",
        preset,

        "-crf",
        str(crf),

        # ================================
        # FASTSTART
        # ================================

        "-movflags",
        "+faststart",

        # ================================
        # OUTPUT
        # ================================

        str(
            output_file.resolve()
        )
    ]

    # =====================================
    # LOG
    # =====================================

    print(
        "[RenderVideo] "
        "Rendering template video..."
    )

    print(
        "[RenderVideo] "
        f"Concat: "
        f"{concat_file}"
    )

    print(
        "[RenderVideo] "
        f"Output: "
        f"{output_file}"
    )

    # =====================================
    # EXECUTE
    # =====================================

    process = subprocess.run(

        cmd,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True
    )

    # =====================================
    # VALIDATE
    # =====================================

    if process.returncode != 0:

        raise RuntimeError(

            "[RenderVideo] "
            "FFmpeg failed\n\n"

            f"STDOUT:\n"
            f"{process.stdout}\n\n"

            f"STDERR:\n"
            f"{process.stderr}"
        )

    if not output_file.exists():

        raise FileNotFoundError(
            f"Output video missing: "
            f"{output_file}"
        )

    file_size = (
        output_file.stat()
        .st_size
    )

    if file_size <= 0:

        raise ValueError(
            "Rendered video is empty"
        )

    # =====================================
    # DONE
    # =====================================

    print(
        "[RenderVideo] "
        f"Completed: "
        f"{output_file}"
    )

    print(
        "[RenderVideo] "
        f"Size: "
        f"{round(file_size / 1024 / 1024, 2)} MB"
    )

    return output_file