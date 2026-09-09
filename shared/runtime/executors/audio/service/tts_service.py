from pathlib import Path
from typing import Optional
import wave

from piper.voice import PiperVoice

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

            for chunk in self._voice.synthesize(text):
                wav.writeframes(
                    chunk.audio_int16_bytes
                )

                frame_count += (
                    len(chunk.audio_int16_bytes)
                    // 2
                )

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
            length_scale=1.0,
        )