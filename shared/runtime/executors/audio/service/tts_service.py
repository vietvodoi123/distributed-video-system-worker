import asyncio
import threading
from pathlib import Path
from typing import Optional
import wave

from piper.voice import PiperVoice
from piper.config import SynthesisConfig

from .models import (
    TTSOptions,
    TTSResult,
)


class TTSService:

    def __init__(
        self,
        *,
        model_path: str | Path,
        config_path: str | Path | None = None,
        use_cuda: bool = False,
        max_concurrency: int = 3,
    ):
        self.model_path = Path(model_path)

        if config_path is None:
            config_path = Path(
                f"{self.model_path}.json"
            )
        else:
            config_path = Path(config_path)

        self.config_path = config_path

        self._voice = PiperVoice.load(
            model_path=self.model_path,
            config_path=self.config_path,
            use_cuda=use_cuda,
        )

        self.sample_rate = (
            self._voice.config.sample_rate
        )
        self.max_concurrency = max_concurrency
        self._inference_lock = threading.Lock()
        self._async_semaphore: Optional[asyncio.Semaphore] = None

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._async_semaphore is None:
            self._async_semaphore = asyncio.Semaphore(self.max_concurrency)
        return self._async_semaphore

    async def synthesize_text_async(
        self,
        *,
        text: str,
        output_file: str | Path,
        options: Optional[TTSOptions] = None,
    ) -> TTSResult:
        """
        Thread-safe async synthesis bounded by worker-level shared concurrency semaphore.
        """
        semaphore = self._get_semaphore()
        async with semaphore:
            return await asyncio.to_thread(
                self.synthesize_text,
                text=text,
                output_file=output_file,
                options=options,
            )

    def synthesize_text(
        self,
        *,
        text: str,
        output_file: str | Path,
        options: Optional[TTSOptions] = None,
    ) -> TTSResult:

        options = (
            options
            if options is not None
            else TTSOptions()
        )

        text = text.strip()

        if not text:
            raise ValueError(
                "Cannot synthesize empty text"
            )

        output_file = Path(output_file)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Calculate length_scale from speed (e.g. speed=1.5 -> length_scale=0.667)
        length_scale = 1.0 / options.speed if options.speed > 0 else 1.0

        syn_config = SynthesisConfig(
            length_scale=length_scale,
            volume=options.volume,
        )

        # Thread-safe ONNX inference
        with self._inference_lock:
            chunks = list(
                self._voice.synthesize(
                    text,
                    syn_config=syn_config,
                )
            )

        frame_count = 0

        with wave.open(
            str(output_file),
            "wb",
        ) as wav:

            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(
                self.sample_rate
            )

            for chunk in chunks:
                wav.writeframes(
                    chunk.audio_int16_bytes
                )

                frame_count += (
                    len(chunk.audio_int16_bytes)
                    // 2
                )

            # Optional sentence silence padding
            if options.sentence_silence > 0:
                silence_frames = int(
                    options.sentence_silence * self.sample_rate
                )
                if silence_frames > 0:
                    wav.writeframes(b"\x00\x00" * silence_frames)
                    frame_count += silence_frames

        duration = (
            frame_count
            / self.sample_rate
        )

        return TTSResult(
            output_file=output_file,
            sample_rate=self.sample_rate,
            channels=1,
            sample_width=2,
            frame_count=frame_count,
            duration=duration,
            speed=options.speed,
            length_scale=length_scale,
        )