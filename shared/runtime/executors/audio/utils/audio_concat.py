import json
import subprocess
from pathlib import Path


LOUDNORM_TARGET = {
    "I": "-14",
    "LRA": "7",
    "TP": "-1.0",
}


async def concat_wav_files(
    *,
    input_files: list[str],
    output_file: str,
    workspace_dir: Path
):

    if not input_files:
        raise ValueError(
            "No input wav files provided"
        )

    concat_file = (
        workspace_dir / "concat.txt"
    )

    lines = []

    for path in input_files:

        safe_path = (
            Path(path)
            .resolve()
            .as_posix()
        )

        lines.append(
            f"file '{safe_path}'"
        )

    concat_file.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    temp_output = (
        workspace_dir / "merged_tmp.wav"
    )

    #
    # Pass 1
    #
    analyze_cmd = [

        "ffmpeg",

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-af",
        (
            f"loudnorm="
            f"I={LOUDNORM_TARGET['I']}:"
            f"LRA={LOUDNORM_TARGET['LRA']}:"
            f"TP={LOUDNORM_TARGET['TP']}:"
            "print_format=json"
        ),

        "-f",
        "null",

        "-"
    ]

    analyze = subprocess.run(
        analyze_cmd,
        capture_output=True,
        text=True
    )

    if analyze.returncode != 0:
        raise RuntimeError(
            analyze.stderr
        )

    stderr = analyze.stderr

    begin = stderr.rfind("{")
    end = stderr.rfind("}")

    if begin == -1 or end == -1:
        raise RuntimeError(
            "Cannot parse loudnorm analysis."
        )

    stats = json.loads(
        stderr[begin:end + 1]
    )

    #
    # Pass 2
    #
    normalize_filter = (
        f"loudnorm="
        f"I={LOUDNORM_TARGET['I']}:"
        f"LRA={LOUDNORM_TARGET['LRA']}:"
        f"TP={LOUDNORM_TARGET['TP']}:"
        f"measured_I={stats['input_i']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:"
        "linear=true"
    )

    cmd = [

        "ffmpeg",

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-af",
        normalize_filter,

        "-c:a",
        "pcm_s16le",

        str(temp_output)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr
        )

    temp_output.replace(output_file)

    if not Path(output_file).exists():
        raise FileNotFoundError(
            f"Merged output missing: {output_file}"
        )