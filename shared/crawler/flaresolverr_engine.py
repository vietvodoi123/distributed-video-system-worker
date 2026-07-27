import httpx

from shared.crawler.base_engine import BaseCrawlerEngine


class FlareSolverrEngine(BaseCrawlerEngine):

    def __init__(
        self,
        endpoint: str = "http://100.78.251.94:8191/v1",
        session: str | None = None,
        timeout: int = 60000,
        **kwargs
    ):
        super().__init__(**kwargs)

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