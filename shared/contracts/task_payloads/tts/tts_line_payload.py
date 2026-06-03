from dataclasses import dataclass


@dataclass
class TtsLinePayload:

    line_index: int

    text: str

    voice: str

    output_name: str