import subprocess
import os
import math
from pathlib import Path


def create_scrolling_text_video(
    text: str,
    total_duration: float,
    font_size: int = 28,
    speed: int = 120,
    y_position: int = 20,
    resolution=(1280, 100),
    font_color="white",
    bg_opacity=0.35,
    output_path="scrolling_text.mp4",
    font_path: str | Path | None = None,
    use_gpu=False,
):
    """
    Production version:
    - Encode 1 lần duy nhất
    - Không loop
    - Không temp file
    - Ổn định cho video 10h+
    """
    if font_path is None or "MAY1" in str(font_path):
        default_font = Path(__file__).resolve().parents[2] / "fonts" / "Anton-Regular.ttf"
        font_path = str(default_font)
    else:
        font_path = str(font_path)

    font_path = (
        font_path
        .replace("\\", "/")
        .replace(":", r"\:")
    )

    if not total_duration:
        raise ValueError("total_duration không hợp lệ")

    duration = math.ceil(float(total_duration))
    width, height = resolution

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ===== Escape text an toàn tuyệt đối =====
    escaped_text = (
        text.replace("\\", "\\\\")
            .replace(":", r"\:")
            .replace("'", r"\'")
            .replace("\n", " ")
    )

    # ===== Background =====
    bg_filter = f"color=c=black@{bg_opacity}:s={width}x{height}:d={duration}"

    # ===== Drawtext scroll =====
    drawtext = (
        f"drawtext="
        f"fontfile='{font_path}':"
        f"text='{escaped_text}':"
        f"fontcolor={font_color}:"
        f"fontsize={font_size}:"
        f"x=w-mod(t*{speed}\\,w+tw):"
        f"y={y_position}:"
        f"borderw=2:"
        f"bordercolor=black"
    )

    filter_chain = drawtext

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", bg_filter,
        "-vf", filter_chain,
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",   # ⚡ tối ưu playback web
    ]

    # ===== Encoder =====
    if use_gpu:
        cmd += [
            "-c:v", "h264_nvenc",
            "-preset", "p1",       # RTX 3060 tối ưu speed/quality
            "-rc", "vbr",
            "-b:v", "2M",
            "-maxrate", "4M",
            "-bufsize", "8M",
        ]
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",   # production nên veryfast
            "-crf", "23",
        ]

    cmd.append(output_path)
    cmd = [str(x) for x in cmd]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    stderr = stderr.decode(
        "utf-8",
        errors="ignore"
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed creating scroll text\n\n{stderr}"
        )

    print(f"✅ Scroll video created: {output_path} ({duration}s)")

    return output_path
