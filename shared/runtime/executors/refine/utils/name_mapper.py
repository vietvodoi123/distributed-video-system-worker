import json

from pathlib import Path


class NameMapper:

    def __init__(
        self,
        *glossary_paths: str
    ):

        self.mapping = {}

        for path in glossary_paths:

            self._load_glossary(path)

    def _load_glossary(
        self,
        path: str
    ):

        glossary_path = Path(path)

        if not glossary_path.exists():
            return

        data = json.loads(
            glossary_path.read_text(
                encoding="utf-8"
            )
        )

        self.mapping.update(data)

    def replace(
        self,
        text: str
    ) -> str:

        for source in sorted(
            self.mapping.keys(),
            key=len,
            reverse=True
        ):

            target = (
                self.mapping[source]
            )

            text = text.replace(
                source,
                target
            )

        return text