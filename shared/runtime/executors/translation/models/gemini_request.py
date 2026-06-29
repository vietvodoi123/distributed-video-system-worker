from dataclasses import dataclass


@dataclass(slots=True)
class GeminiRequest:
    """
    Request gửi tới Gemini.
    """

    prompt: str

    system_prompt: str | None = None

    temperature: float = 0.0

    max_output_tokens: int | None = None

    response_mime_type: str | None = None