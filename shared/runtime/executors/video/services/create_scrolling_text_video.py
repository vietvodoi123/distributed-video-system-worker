import subprocess
import os
import math
import shlex


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
    font_path=r"C\:/Users/HLC/PycharmProjects/automation_make_video_v2/fonts/Anton-Regular.ttf",
    use_gpu=False,
):
    """
    Production version:
    - Encode 1 lần duy nhất
    - Không loop
    - Không temp file
    - Ổn định cho video 10h+
    """

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
        print("⚡ NVENC enabled (preset p4)")
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",   # production nên veryfast
            "-crf", "23",
        ]
        print("🧠 CPU encode (veryfast)")

    cmd.append(output_path)

    print("▶️ Creating scrolling text video...")

    # ⚠️ Không dùng subprocess.run PIPE ở đây
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    process.wait()

    if process.returncode != 0:
        raise RuntimeError("FFmpeg failed creating scroll text")

    print(f"✅ Scroll video created: {output_path} ({duration}s)")

    return output_path
