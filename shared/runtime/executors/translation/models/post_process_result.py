from dataclasses import dataclass
from enum import Enum


class PostProcessAction(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"


@dataclass(slots=True)
class PostProcessResult:

    action: PostProcessAction

    text: str

    reason: str | None = None