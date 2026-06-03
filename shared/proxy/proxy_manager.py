from shared.proxy.static_proxy_provider import (
    StaticProxyProvider
)

from shared.proxy.rotate_proxy_provider import (
    RotateProxyProvider
)


class ProxyManager:

    def __init__(self):

        self.providers = {}

    def register_provider(
        self,
        name: str,
        provider
    ):

        self.providers[name] = provider

    def get_proxy(
        self,
        provider_name: str | None
    ) -> dict | None:

        if not provider_name:
            return None

        provider = (
            self.providers.get(
                provider_name
            )
        )

        if not provider:
            return None

        return provider.get_proxy()