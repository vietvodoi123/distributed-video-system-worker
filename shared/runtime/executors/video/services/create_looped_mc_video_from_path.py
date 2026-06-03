import os
import subprocess


def create_looped_mc_video_from_path(
    local_input_path,
    output_path,
    duration
):

    local_input_path = str(
        local_input_path
    )

    output_path = str(
        output_path
    )

    if not os.path.exists(
        local_input_path
    ):

        raise FileNotFoundError(
            f"❌ Không tìm thấy file: "
            f"{local_input_path}"
        )

    if duration is None:

        raise ValueError(
            "❌ duration không được None"
        )

    duration = int(duration)

    cmd = [

        "ffmpeg",

        "-y",

        # debug dễ hơn
        "-loglevel",
        "error",

        "-ss",
        "0",

        "-i",
        local_input_path,

        "-t",
        str(duration),

        "-map",
        "0:v:0",

        "-an",

        # reset pts + resize chuẩn
        "-vf",
        (
            "setpts=PTS-STARTPTS,"
            "scale=264:-1,"
        ),

        # =================================
        # CPU ENCODER
        # =================================

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        output_path
    ]



    subprocess.run(
        cmd,
        check=True
    )

    return output_path