from shared.proxy.base_proxy_provider import (
    BaseProxyProvider
)


class StaticProxyProvider(
    BaseProxyProvider
):

    def __init__(
        self,
        proxies: list[str]
    ):

        self.proxies = proxies
        self.index = 0

    def get_proxy(
        self
    ) -> dict | None:

        if not self.proxies:
            return None

        proxy = (
            self.proxies[
                self.index % len(self.proxies)
            ]
        )

        self.index += 1

        return {
            "http": proxy,
            "https": proxy
        }