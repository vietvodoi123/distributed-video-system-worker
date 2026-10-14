
from dataclasses import dataclass
from shared.config.settings import settings
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

        use_gpu: bool = False,

        audio_path: str | None = None
    ):
        vr = getattr(settings, "video_render", None)
        if vr:
            if vr.acceleration == "nvenc":
                use_gpu = True
            elif vr.acceleration == "cpu":
                use_gpu = False

        nvenc_preset = vr.nvenc_preset if vr else "p1"
        nvenc_cq = vr.nvenc_cq if vr else 27
        cpu_preset = vr.cpu_preset if vr else "ultrafast"
        cpu_crf = vr.cpu_crf if vr else 27
        target_bitrate = vr.target_bitrate if vr else "2M"
        max_bitrate = vr.max_bitrate if vr else "3M"
        bufsize = vr.bufsize if vr else "6M"

        # =====================================
        # INPUTS
        # =====================================

        base_str = str(base_video)
        if base_str.endswith(".txt"):
            inputs = ["-f", "concat", "-safe", "0", "-i", base_str]
        else:
            inputs = ["-i", base_str]

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
                or
                layer.height is not None
            ):
                w = layer.width if layer.width is not None else -1
                h = layer.height if layer.height is not None else -1

                chain += (
                    f",scale="
                    f"{w}:"
                    f"{h}"
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
            # OVERLAY
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
            f"format=yuv420p[vout]"
        )

        filter_complex = ";".join(
            filter_parts
        )

        # =====================================
        # AUDIO INPUT (IF PROVIDED)
        # =====================================

        if audio_path:
            inputs.extend([
                "-i", str(audio_path)
            ])
            audio_index = len(overlays) + 1

        # =====================================
        # COMMAND
        # =====================================

        cmd = [

            "ffmpeg",

            "-y",

            "-loglevel",
            "info",

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

        if audio_path:
            cmd.extend([
                "-map",
                f"{audio_index}:a",

                "-c:a",
                "aac",

                "-b:a",
                "192k",

                "-shortest"
            ])

        # =====================================
        # ENCODER
        # =====================================

        if use_gpu:

            # =================================
            # NVIDIA NVENC
            # =================================

            cmd += [

                "-c:v",
                "h264_nvenc",

                "-preset",
                nvenc_preset,

                "-profile:v",
                "high",

                "-pix_fmt",
                "yuv420p",

                "-rc",
                "vbr",

                "-cq",
                str(nvenc_cq),

                "-b:v",
                target_bitrate,

                "-maxrate",
                max_bitrate,

                "-bufsize",
                bufsize
            ]

        else:

            # =================================
            # CPU / LIBX264
            # =================================

            cmd += [

                "-threads",
                "0",

                "-c:v",
                "libx264",

                "-preset",
                cpu_preset,

                "-crf",
                str(cpu_crf),

                "-pix_fmt",
                "yuv420p"
            ]

        # =====================================
        # OUTPUT
        # =====================================

        cmd += [

            "-movflags",
            "+faststart",

            "-max_muxing_queue_size",
            "4096",

            str(output_path)
        ]

        # =====================================
        # LOG
        # =====================================

        print(
            "[VideoLayerComposer] "
            "Composing video..."
        )

        print(
            "[VideoLayerComposer] "
            f"Base: {base_video}"
        )

        print(
            "[VideoLayerComposer] "
            f"Overlays: {len(overlays)}"
        )

        print(
            "[VideoLayerComposer] "
            f"Output: {output_path}"
        )

        if use_gpu:

            print(
                "[VideoLayerComposer] "
                "Encoder: NVIDIA NVENC (h264_nvenc)"
            )

        else:

            print(
                "[VideoLayerComposer] "
                "Encoder: CPU (libx264)"
            )

        # =====================================
        # EXECUTE
        # =====================================

        run_ffmpeg_with_progress(
            cmd
        )

        # =====================================
        # VALIDATE
        # =====================================

        return output_path

