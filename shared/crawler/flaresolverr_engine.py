import os
import httpx

from shared.config.settings import settings
from shared.crawler.base_engine import BaseCrawlerEngine


class FlareSolverrEngine(BaseCrawlerEngine):

    def __init__(
        self,
        endpoint: str | None = None,
        session: str | None = None,
        timeout: int = 60000,
        **kwargs
    ):
        super().__init__(**kwargs)

        if not endpoint:
            endpoint = (
                os.getenv("FLARESOLVERR_URL")
                or getattr(getattr(settings, "crawler", None), "flaresolverr_url", None)
                or getattr(settings.api, "flaresolverr", None)
                or "http://localhost:8191/v1"
            )

        endpoint = str(endpoint).strip().rstrip("/")
        if not endpoint.endswith("/v1"):
            endpoint = f"{endpoint}/v1"

        self.endpoint = endpoint
        self.session = session
        self.timeout = timeout

    async def get_html(
        self,
        url: str,
        **kwargs
    ) -> str:

        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": self.timeout,
        }

        if self.session:
            payload["session"] = self.session

        async with httpx.AsyncClient(
            timeout=180
        ) as client:

            resp = await client.post(
                self.endpoint,
                json=payload
            )

        resp.raise_for_status()

        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(data)

        return data["solution"]["response"]

    async def get_json(
        self,
        url: str,
        **kwargs
    ):
        raise NotImplementedError(
            "FlareSolverr only supports HTML crawling."
        )
