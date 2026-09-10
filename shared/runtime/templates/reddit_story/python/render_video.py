
import subprocess
from pathlib import Path


def create_video_from_concat(
    concat_file: str,
    output_file: str,
    fps: int = 8,
    codec: str = "libx264",
    preset: str = "medium",
    crf: int = 18,
    use_gpu: bool = False,
):
    """
    Render MP4 video from FFmpeg concat.txt.

    Khi use_gpu=True:
        Sử dụng NVIDIA NVENC (h264_nvenc) để encode video.

    Khi use_gpu=False:
        Giữ nguyên libx264 như behavior hiện tại.
    """

    concat_file = Path(concat_file)
    output_file = Path(output_file)

    # =====================================
    # VALIDATE
    # =====================================

    if not concat_file.exists():
        raise FileNotFoundError(
            f"Concat file not found: {concat_file}"
        )

    concat_content = concat_file.read_text(
        encoding="utf-8"
    ).strip()

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
        str(concat_file.resolve()),

        # ================================
        # VIDEO
        # ================================

        "-vsync",
        "vfr",

        "-pix_fmt",
        "yuv420p",
    ]

    # =====================================
    # VIDEO ENCODER
    # =====================================

    if use_gpu:

        # NVIDIA NVENC
        cmd += [
            "-c:v",
            "h264_nvenc",

            # NVENC preset:
            # p1 = fastest
            # p4 = balanced
            # p5 = better quality
            "-preset",
            "p4",

            "-pix_fmt",
            "yuv420p",

            # Constant quality mode
            "-rc",
            "vbr",

            "-cq",
            str(crf),

            # Giới hạn bitrate để tránh bitrate tăng quá cao
            "-b:v",
            "4M",

            "-maxrate",
            "6M",

            "-bufsize",
            "12M",
        ]

    else:

        # CPU / libx264
        cmd += [
            "-c:v",
            codec,

            "-preset",
            preset,

            "-crf",
            str(crf),
        ]

    # =====================================
    # FASTSTART
    # =====================================

    cmd += [
        "-movflags",
        "+faststart",

        # ================================
        # OUTPUT
        # ================================

        str(output_file.resolve()),
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
        f"Concat: {concat_file}"
    )

    print(
        "[RenderVideo] "
        f"Output: {output_file}"
    )

    if use_gpu:
        print(
            "[RenderVideo] "
            "Encoder: NVIDIA NVENC (h264_nvenc)"
        )
    else:
        print(
            "[RenderVideo] "
            f"Encoder: {codec}"
        )

    # =====================================
    # EXECUTE
    # =====================================

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
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
            f"Output video missing: {output_file}"
        )

    file_size = output_file.stat().st_size

    if file_size <= 0:

        raise ValueError(
            "Rendered video is empty"
        )

    # =====================================
    # DONE
    # =====================================

    print(
        "[RenderVideo] "
        f"Completed: {output_file}"
    )

    print(
        "[RenderVideo] "
        f"Size: "
        f"{round(file_size / 1024 / 1024, 2)} MB"
    )

    return output_file

