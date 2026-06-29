from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ApiKeyState(str, Enum):
    FREE = "free"
    BUSY = "busy"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


@dataclass(slots=True)
class GeminiApiKey:
    id: int
    api_key: str

    state: ApiKeyState = ApiKeyState.FREE

    cooldown_until: datetime | None = None

    consecutive_errors: int = 0

    total_requests: int = 0

    total_errors: int = 0

    @property
    def display_name(self) -> str:
        return (
            f"Key#{self.id}"
            f" ({self.api_key[:8]}...{self.api_key[-4:]})"
        )