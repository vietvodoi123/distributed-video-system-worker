import asyncio
import json
import wave
from pathlib import Path


LOUDNORM_TARGET = {
    "I": "-14",
    "LRA": "7",
    "TP": "-1.0",
}


def native_concat_wav_files(
    input_files: list[str | Path],
    output_file: str | Path,
) -> float:
    """
    Concatenate WAV files directly by reading raw PCM frames.
    Extremely fast (< 0.1s) and strictly preserves frame-accurate timing.
    Returns total duration in seconds.
    """
    if not input_files:
        raise ValueError("No input wav files provided")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter out missing or empty files
    valid_files = []
    params = None

    for f in input_files:
        p = Path(f)
        if p.exists() and p.stat().st_size > 44:
            try:
                with wave.open(str(p), "rb") as w_check:
                    if w_check.getnframes() > 0:
                        if params is None:
                            params = w_check.getparams()
                        valid_files.append(p)
            except Exception as e:
                print(f"[audio_concat] Warning: skipping invalid wav file {p}: {e}")

    if not valid_files or params is None:
        raise ValueError("No valid audio frames found in input wav files")

    sample_rate = params.framerate
    total_frames = 0
    with wave.open(str(output_path), "wb") as w_out:
        w_out.setparams(params)
        for f_path in valid_files:
            with wave.open(str(f_path), "rb") as w_in:
                n_frames = w_in.getnframes()
                total_frames += n_frames
                frames = w_in.readframes(n_frames)
                w_out.writeframes(frames)

    return total_frames / sample_rate


async def apply_loudnorm_async(
    input_wav: Path,
    output_wav: Path,
) -> bool:
    """
    Apply FFmpeg 2-pass Loudnorm asynchronously without blocking the event loop.
    Returns True if successful, False otherwise.
    """
    try:
        # Pass 1: Analysis
        analyze_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_wav),
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
            "-",
        ]

        proc = await asyncio.create_subprocess_exec(
            *analyze_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr_bytes = await proc.communicate()

        if proc.returncode != 0:
            return False

        stderr = stderr_bytes.decode("utf-8", errors="ignore")
        begin = stderr.rfind("{")
        end = stderr.rfind("}")

        if begin == -1 or end == -1:
            return False

        stats = json.loads(stderr[begin : end + 1])

        # Pass 2: Normalize
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

        norm_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_wav),
            "-af",
            normalize_filter,
            "-c:a",
            "pcm_s16le",
            str(output_wav),
        ]

        proc_norm = await asyncio.create_subprocess_exec(
            *norm_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc_norm.communicate()

        return proc_norm.returncode == 0 and output_wav.exists()
    except Exception as e:
        print(f"[audio_concat] Loudnorm error: {e}")
        return False


async def concat_wav_files(
    *,
    input_files: list[str | Path],
    output_file: str | Path,
    workspace_dir: Path,
    use_gpu: bool = False,
    apply_loudnorm: bool = False,
):
    if not input_files:
        raise ValueError("No input wav files provided")

    output_path = Path(output_file)
    workspace_path = Path(workspace_dir)

    # 1. Direct Native Python Wave Concatenation (instantaneous, 100% exact timing)
    if not apply_loudnorm:
        await asyncio.to_thread(native_concat_wav_files, input_files, output_path)
        if not output_path.exists() or output_path.stat().st_size <= 44:
            raise RuntimeError(f"Merged output missing or empty: {output_path}")
        return

    # 2. Optional Async Loudnorm
    temp_raw = workspace_path / "merged_raw.wav"
    await asyncio.to_thread(native_concat_wav_files, input_files, temp_raw)

    temp_norm = workspace_path / "merged_norm.wav"
    success = await apply_loudnorm_async(temp_raw, temp_norm)
    if success and temp_norm.exists() and temp_norm.stat().st_size > 44:
        if output_path.exists():
            output_path.unlink()
        temp_norm.replace(output_path)
        if temp_raw.exists():
            temp_raw.unlink(missing_ok=True)
    else:
        if output_path.exists():
            output_path.unlink()
        temp_raw.replace(output_path)