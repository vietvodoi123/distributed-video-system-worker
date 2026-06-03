from pathlib import Path

import httpx


class OllamaTranslateService:

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b-instruct"
    ):

        self.base_url = base_url
        self.model = model
        self.prompt_template = (
            self._load_prompt()
        )

    def _load_prompt(self) -> str:

        prompt_path = (
            Path(__file__)
            .resolve()
            .parents[1]
            / "prompts"
            / "zh_to_vi.txt"
        )

        return prompt_path.read_text(
            encoding="utf-8"
        )
    async def translate(
        self,
        text: str
    ) -> str:

        prompt = self._build_prompt(
            text
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "5m",
            "options" :{
                "temperature": 0.6,
                "top_p": 0.9,
                "repeat_penalty": 1.05,
                "num_predict": 1024,
                "num_ctx": 2048,
            }
        }

        async with httpx.AsyncClient(
            timeout=300
        ) as client:

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )

        response.raise_for_status()

        data = response.json()

        translated = (
            data
            .get("response", "")
            .strip()
        )

        return translated

    def _build_prompt(
            self,
            text: str
    ) -> str:
        return (
            self.prompt_template
            .replace(
                "{{text}}",
                text
            )
        )

    async def unload_model(self):

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "keep_alive": 0
                }
            )