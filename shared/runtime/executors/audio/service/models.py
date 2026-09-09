from dataclasses import dataclass
import math

@dataclass(frozen=True)
class TTSOptions:
    """
    Các tùy chọn điều khiển quá trình TTS.

    speed:
        1.0 = tốc độ mặc định.
        > 1.0 = nhanh hơn.
        < 1.0 = chậm hơn.

    volume:
        Hệ số âm lượng mong muốn.
        Hiện tại không được áp dụng trong TTSService.
        AudioExecutor sẽ xử lý volume bằng FFmpeg.

    sentence_silence:
        Số giây im lặng sau mỗi câu.
    """

    speed: float = 1.0
    volume: float = 1.0
    sentence_silence: float = 0.0

    def __post_init__(self):

        if not math.isfinite(self.speed) or self.speed <= 0:
            raise ValueError(
                "TTS speed must be a finite value greater than 0"
            )

        if not math.isfinite(self.volume) or self.volume < 0:
            raise ValueError(
                "TTS volume must be a finite value greater than or equal to 0"
            )

        if (
                not math.isfinite(self.sentence_silence)
                or self.sentence_silence < 0
        ):
            raise ValueError(
                "TTS sentence silence must be a finite value greater than or equal to 0"
            )

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TTSResult:

    output_file: Path

    sample_rate: int

    channels: int

    sample_width: int

    frame_count: int

    duration: float

    speed: float

    length_scale: float