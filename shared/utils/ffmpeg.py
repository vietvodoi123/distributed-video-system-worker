# shared/utils/ffmpeg.py

from pathlib import Path
import os
import shutil


def setup_ffmpeg():

    project_root = Path(__file__).resolve().parents[2]

    ffmpeg_dir = (
        project_root /
        "ffmpeg"
    )

    paths_to_add = []
    if ffmpeg_dir.exists():
        paths_to_add.append(str(ffmpeg_dir))

    # Đảm bảo Node.js luôn có trong PATH của tiến trình
    node_default = Path(r"C:\Program Files\nodejs")
    if node_default.exists() and not shutil.which("node"):
        paths_to_add.append(str(node_default))

    if paths_to_add:
        os.environ["PATH"] = os.pathsep.join(paths_to_add) + os.pathsep + os.environ["PATH"]
