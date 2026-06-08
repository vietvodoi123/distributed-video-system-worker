# shared/utils/ffmpeg.py

from pathlib import Path
import os


def setup_ffmpeg():

    project_root = Path(__file__).resolve().parents[2]

    ffmpeg_dir = (
        project_root /
        "ffmpeg"
    )

    os.environ["PATH"] = (
        str(ffmpeg_dir)
        + os.pathsep
        + os.environ["PATH"]
    )