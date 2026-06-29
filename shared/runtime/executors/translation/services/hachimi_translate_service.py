import asyncio
import os
from pathlib import Path

from shared.runtime.executors.translation.scripts.translator import HachimiTranslator


class HachimiTranslateService:

    _translator = None

    def __init__(self):
        if self.__class__._translator is None:
            self.__class__._translator = self._load()

    def _load(self):
        project_root = Path(__file__).resolve().parents[5]

        os.environ["HACHIMIMT_MODELS_DIR"] = str(
            project_root
            / "shared"
            / "runtime"
            / "executors"
            / "translation"
            / "models"
        )

        translator = HachimiTranslator()

        print(
            translator.load("HachimiMT-60")
        )

        return translator

    async def translate(
            self,
            text: str,
    ) -> str:
        loop = asyncio.get_running_loop()

        def _translate():
            translated_lines = []

            for line in text.split("\n"):
                line = line.strip()

                if not line:
                    translated_lines.append("")
                    continue

                _, translated = self._translator.translate_text(
                    line,
                    chunk_mode="sentence",
                    beam_size=1,
                )

                translated_lines.append(translated)

            return "\n".join(translated_lines)

        return await loop.run_in_executor(
            None,
            _translate,
        )


import asyncio

async def main():
    translator = HachimiTranslateService()

    text = "你好"

    translated = await translator.translate(text)

    print(translated)

if __name__ == "__main__":
    asyncio.run(main())