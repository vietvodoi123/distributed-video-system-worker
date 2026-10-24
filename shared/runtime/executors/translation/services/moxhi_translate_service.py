import httpx
from shared.config.settings import settings


class MoxhiTranslateService:

    HEADERS = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    def __init__(self, base_url: str | None = None):
        raw_url = (base_url or settings.api.translate_moxhi or "http://192.168.1.147:8090").strip().rstrip("/")
        if raw_url.endswith("/translate"):
            self.TRANSLATE_URL = raw_url
            self.BASE_URL = raw_url[:-len("/translate")].rstrip("/")
        else:
            self.BASE_URL = raw_url
            self.TRANSLATE_URL = f"{raw_url}/translate"

    async def translate(
        self,
        text: str,
        text_type: str = "Ancient",
    ) -> str:

        if not text or not text.strip():
            return ""

        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            response = await client.post(
                self.TRANSLATE_URL,
                headers=self.HEADERS,
                json={
                    "text": text
                },
            )

        response.raise_for_status()

        result = response.json()

        if not result.get("ok"):

            raise ValueError(
                f"Moxhi translation failed: {result}"
            )

        return (
            result
            .get("text", "")
            .strip()
        )
