from pathlib import Path


def generate_frames_concat_from_segments(

    segments: list[dict],

    frames_dir: Path,

    output_concat_path: Path,
):

    """
    Generate FFmpeg concat.txt directly from segments.

    Segment format:

    [
        {
            "line_index": 0,
            "line_text": "...",
            "start_time": 0,
            "end_time": 2500,
            "duration": 2500,
        }
    ]
    """

    frames_dir = Path(
        frames_dir
    )

    output_concat_path = Path(
        output_concat_path
    )

    # =====================================
    # VALIDATE
    # =====================================

    if not frames_dir.exists():

        raise FileNotFoundError(
            f"Frames directory not found: "
            f"{frames_dir}"
        )

    if not segments:

        raise ValueError(
            "No segments provided."
        )

    # =====================================
    # SORT SEGMENTS
    # =====================================

    segments = sorted(

        segments,

        key=lambda s: s["line_index"]
    )

    # =====================================
    # BUILD CONCAT
    # =====================================

    lines = []

    for segment in segments:

        index = int(
            segment["line_index"]
        )

        duration = float(
            segment["duration"]
        )

        if duration <= 0:

            raise ValueError(
                f"Invalid duration "
                f"for segment {index}"
            )

        frame_path = (
            frames_dir
            / f"frame{index:04d}.jpg"
        )

        if not frame_path.exists():

            raise FileNotFoundError(
                f"Missing frame: "
                f"{frame_path}"
            )

        frame_path_ffmpeg = (
            str(
                frame_path.resolve()
            )
            .replace("\\", "/")
        )

        lines.append(
            f"file '{frame_path_ffmpeg}'"
        )

        lines.append(
            f"duration {duration:.6f}"
        )

    # =====================================
    # DUPLICATE LAST FRAME
    # =====================================

    lines.append(
        lines[-2]
    )

    # =====================================
    # WRITE OUTPUT
    # =====================================

    output_concat_path.parent.mkdir(

        parents=True,

        exist_ok=True
    )

    output_concat_path.write_text(

        "\n".join(lines),

        encoding="utf-8"
    )

    return output_concat_path