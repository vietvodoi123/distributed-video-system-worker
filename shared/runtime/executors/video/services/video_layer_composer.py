from dataclasses import dataclass

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_with_progress
)


@dataclass
class OverlayLayer:

    path: str

    x: int
    y: int

    width: int | None = None
    height: int | None = None

    opacity: float = 1.0


class VideoLayerComposer:

    def compose(

        self,

        base_video: str,

        overlays: list[OverlayLayer],

        output_path: str,

        use_gpu: bool = True
    ):

        inputs = [
            "-i", str(base_video)
        ]

        filter_parts = []

        # =====================================
        # BASE
        # =====================================

        filter_parts.append(
            "[0:v]"
            "setpts=PTS-STARTPTS,"
            "fps=8"
            "[base]"
        )

        current = "[base]"

        # =====================================
        # OVERLAYS
        # =====================================

        for idx, layer in enumerate(overlays):

            input_index = idx + 1

            inputs.extend([
                "-stream_loop",
                "-1",

                "-i",
                str(layer.path)
            ])

            layer_tag = f"layer{idx}"

            chain = (
                f"[{input_index}:v]"
                f"setpts=PTS-STARTPTS"
            )

            # =================================
            # OPTIONAL SCALE
            # =================================

            if (
                layer.width is not None
                and
                layer.height is not None
            ):

                chain += (
                    f",scale="
                    f"{layer.width}:"
                    f"{layer.height}"
                )

            # =================================
            # OPACITY
            # =================================

            if layer.opacity < 1.0:

                chain += (
                    f",format=rgba,"
                    f"colorchannelmixer="
                    f"aa={layer.opacity}"
                )

            chain += f"[{layer_tag}]"

            filter_parts.append(chain)

            output_tag = f"tmp{idx}"

            # =================================
            # IMPORTANT
            # =================================

            overlay = (

                f"{current}"
                f"[{layer_tag}]"

                f"overlay="
                f"x={layer.x}:"
                f"y={layer.y}:"
                f"shortest=0:"
                f"repeatlast=0"

                f"[{output_tag}]"
            )

            filter_parts.append(
                overlay
            )

            current = (
                f"[{output_tag}]"
            )

        # =====================================
        # FINAL
        # =====================================

        filter_parts.append(
            f"{current}"
            f"format=nv12[vout]"
        )

        filter_complex = ";".join(
            filter_parts
        )

        # =====================================
        # COMMAND
        # =====================================

        cmd = [

            "ffmpeg",

            "-y",

            "-loglevel",
            "verbose",

            "-fflags",
            "+genpts",

            "-avoid_negative_ts",
            "make_zero",

            *inputs,

            "-filter_complex",
            filter_complex,

            "-map",
            "[vout]"
        ]

        # =====================================
        # ENCODER
        # =====================================

        if use_gpu:

            cmd += [

                "-c:v",
                "h264_nvenc",

                "-preset",
                "p5",

                "-profile:v",
                "high",

                "-pix_fmt",
                "nv12",

                "-rc",
                "vbr",

                "-cq",
                "23",

                "-b:v",
                "2M"
            ]

        else:

            cmd += [

                "-threads",
                "0",

                "-c:v",
                "libx264",

                "-preset",
                "veryfast",

                "-crf",
                "23"
            ]

        cmd += [

            "-movflags",
            "+faststart",

            "-max_muxing_queue_size",
            "4096",

            str(output_path)
        ]

        run_ffmpeg_with_progress(
            cmd
        )

        return output_path