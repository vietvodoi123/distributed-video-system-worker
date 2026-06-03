from dataclasses import dataclass
from typing import List

from .tts_segment_artifact import (
    TtsSegmentArtifact
)


@dataclass
class TtsBatchManifest:

    group_key: str

    total_segments: int

    segments: List[TtsSegmentArtifact]