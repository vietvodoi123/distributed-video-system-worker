from dataclasses import dataclass


@dataclass
class GenerateTtsSegmentsPayload:

    voice: str = "vi-vn-x-vie-local"