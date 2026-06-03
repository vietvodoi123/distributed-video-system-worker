# shared/runtime/executors/translation/services/dichnhanh_translate_service.py

import httpx

from shared.runtime.executors.translation.utils.extract_text_with_linebreaks import (
    extract_text_with_linebreaks
)


class DichNhanhTranslateService:

    BASE_URL = (
        "https://api.dichnhanh.com/"
    )

    HEADERS = {
        "accept": (
            "application/json, "
            "text/plain, */*"
        ),
        "content-type": (
            "application/x-www-form-urlencoded"
        ),
        "origin": "https://dichnhanh.com",
        "referer": "https://dichnhanh.com/",
        "user-agent": (
            "Mozilla/5.0"
        )
    }

    async def translate(
        self,
        text: str,
        text_type: str = "Ancient"
    ) -> str:

        data = {
            "type": text_type,
            "enable_analyze": "1",
            "enable_fanfic": "0",
            "mode": "vi",
            "text": text
        }

        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            response = await client.post(
                self.BASE_URL,
                headers=self.HEADERS,
                data=data
            )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):

            raise ValueError(
                f"Translation failed: {result}"
            )

        html = (
            result
            .get("data", {})
            .get("content", "")
        )

        return extract_text_with_linebreaks(
            html
        ).strip()