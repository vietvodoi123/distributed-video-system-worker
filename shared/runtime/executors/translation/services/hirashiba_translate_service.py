# shared/runtime/executors/translation/services/hirashiba_translate_service.py

import asyncio
from pathlib import Path

import torch
from transformers import MarianMTModel, MarianTokenizer


class HirashibaTranslateService:

    _model = None
    _tokenizer = None
    _device = None
    _lock = asyncio.Lock()

    MODEL_PATH = (
        Path(__file__).resolve().parents[5]
        / "models"
        / "hirashiba-mt-tiny-zh-vi"
    )

    @classmethod
    async def _load(cls):

        if cls._model is not None:
            return

        async with cls._lock:

            if cls._model is not None:
                return

            cls._device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

            cls._tokenizer = MarianTokenizer.from_pretrained(
                cls.MODEL_PATH
            )

            cls._model = (
                MarianMTModel
                .from_pretrained(cls.MODEL_PATH)
                .to(cls._device)
                .eval()
            )

    async def translate(
        self,
        text: str,
    ) -> str:

        await self._load()

        lines = text.split("\n")

        translated_lines = []

        for line in lines:

            line = line.strip()

            if not line:
                translated_lines.append("")
                continue

            inputs = (
                self._tokenizer(
                    line,
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                )
                .to(self._device)
            )

            with torch.no_grad():

                outputs = self._model.generate(
                    **inputs,
                    max_length=512,
                )

            translated = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
            )

            translated_lines.append(
                translated
            )

        return "\n".join(translated_lines)