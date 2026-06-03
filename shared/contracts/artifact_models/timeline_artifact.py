from dataclasses import dataclass
from typing import List


@dataclass
class TimelineSegment:

    line_index: int

    text: str

    start_time: float

    end_time: float

    duration: float

    audio_path: str


@dataclass
class TimelineArtifact:

    total_duration: float

    total_segments: int

    segments: List[TimelineSegment]