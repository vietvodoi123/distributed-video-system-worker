import subprocess
from pathlib import Path


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

    cmd = [

        "ffmpeg",

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-c",
        "copy",

        output_file
    ]

    result = subprocess.run(

        cmd,

        capture_output=True,

        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(

            "FFmpeg concat failed:\n"
            f"{result.stderr}"
        )

    if not Path(output_file).exists():

        raise FileNotFoundError(
            f"Merged output missing: "
            f"{output_file}"
        )