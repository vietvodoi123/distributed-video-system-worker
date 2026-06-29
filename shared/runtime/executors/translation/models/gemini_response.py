from dataclasses import dataclass


@dataclass(slots=True)
class GeminiResponse:
    """
    Response chuẩn trả về từ Gemini.
    """

    text: str

    finish_reason: str | None = None

    prompt_token_count: int | None = None

    candidates_token_count: int | None = None

    total_token_count: int | None = None