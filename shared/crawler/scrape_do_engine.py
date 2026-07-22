import requests
import urllib.parse

from shared.crawler.base_engine import BaseCrawlerEngine


class ScrapeDoEngine(BaseCrawlerEngine):

    def __init__(
        self,
        token: str
    ):
        self.token = token


    async def get_html(
        self,
        url: str,
        **kwargs
    ) -> str:

        encoded_url = urllib.parse.quote(
            url,
            safe=""
        )

        scrape_url = (
            "https://api.scrape.do/"
            f"?token={self.token}"
            f"&url={encoded_url}"
        )

        response = requests.get(
            scrape_url,
            timeout=60
        )

        response.raise_for_status()

        return response.text


    async def get_json(
        self,
        url: str,
        **kwargs
    ):

        raise NotImplementedError()