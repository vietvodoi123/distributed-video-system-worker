from abc import ABC
from abc import abstractmethod


class BaseProxyProvider(ABC):

    @abstractmethod
    def get_proxy(
        self
    ) -> dict | None:
        pass