import httpx


class MoxhiTranslateService:

    BASE_URL = (
        "http://127.0.0.1:8090"
    )

    TRANSLATE_URL = (
        f"{BASE_URL}/translate"
    )

    HEADERS = {
        "accept": "application/json",
        "content-type": "application/json",
    }

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