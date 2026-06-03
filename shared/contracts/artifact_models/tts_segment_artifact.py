from dataclasses import dataclass


@dataclass
class TtsSegmentArtifact:

    line_index: int

    text: str

    audio_path: str

    duration: float