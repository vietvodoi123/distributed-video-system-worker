from abc import ABC, abstractmethod
from typing import Any


class BaseCrawlerEngine(ABC):

    def __init__(
        self,
        website=None,
        story_source=None
    ):
        self.website = website
        self.story_source = story_source

    @abstractmethod
    async def get_html(
        self,
        url: str,
        **kwargs
    ) -> str:
        pass

    @abstractmethod
    async def get_json(
        self,
        url: str,
        **kwargs
    ) -> dict[str, Any]:
        pass