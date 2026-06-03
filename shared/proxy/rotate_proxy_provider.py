from shared.proxy.base_proxy_provider import (
    BaseProxyProvider
)


class RotateProxyProvider(
    BaseProxyProvider
):

    def __init__(
        self,
        proxy_endpoint: str
    ):

        self.proxy_endpoint = (
            proxy_endpoint
        )

    def get_proxy(
        self
    ) -> dict | None:

        return {
            "http": self.proxy_endpoint,
            "https": self.proxy_endpoint
        }