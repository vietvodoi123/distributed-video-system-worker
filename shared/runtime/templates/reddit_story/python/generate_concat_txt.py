import json

from pathlib import Path


def generate_frames_concat_from_timeline(

    timeline_path: Path,

    frames_dir: Path,

    output_concat_path: Path,
):

    """
    Generate FFmpeg concat.txt from timeline.json

    Timeline format:

    {
        "segments": [
            {
                "index": 0,
                "text": "...",
                "start_time": 0,
                "end_time": 2500
            }
        ]
    }
    """

    timeline_path = Path(
        timeline_path
    )

    frames_dir = Path(
        frames_dir
    )

    output_concat_path = Path(
        output_concat_path
    )

    # =====================================
    # VALIDATE
    # =====================================

    if not timeline_path.exists():

        raise FileNotFoundError(
            f"Timeline not found: "
            f"{timeline_path}"
        )

    if not frames_dir.exists():

        raise FileNotFoundError(
            f"Frames directory not found: "
            f"{frames_dir}"
        )

    # =====================================
    # LOAD TIMELINE
    # =====================================

    timeline_data = json.loads(

        timeline_path.read_text(
            encoding="utf-8"
        )
    )
    
    segments = timeline_data.get(
        "segments",
        []
    )

    if not segments:

        raise ValueError(
            "Timeline has no segments"
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

        index = segment["line_index"]

        start_time = (
            segment["start_time"]
        )

        end_time = (
            segment["end_time"]
        )

        duration = (
            end_time - start_time
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

        # =================================
        # FFMPEG SAFE PATH
        # =================================

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

    # FFmpeg concat demuxer requires
    # final frame duplicated

    lines.append(lines[-2])

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