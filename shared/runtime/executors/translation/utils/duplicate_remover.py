# shared/runtime/executors/translation/utils/duplicate_remover.py

import re
import hashlib


class DuplicateRemover:

    @staticmethod
    def normalize(
        text: str
    ) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"[^\w\s]",
            "",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    @classmethod
    def hash_text(
        cls,
        text: str
    ) -> str:

        return hashlib.md5(
            text.encode("utf-8")
        ).hexdigest()

    @classmethod
    def remove_large_duplicate_blocks(
        cls,
        text: str,
        min_lines: int = 8,
        max_lines: int = 50
    ) -> str:

        lines = [
            l.strip()
            for l in text.splitlines()
            if l.strip()
        ]

        n = len(lines)

        seen = set()

        result = []

        i = 0

        while i < n:

            removed = False

            for size in range(
                max_lines,
                min_lines - 1,
                -1
            ):

                if i + size > n:
                    continue

                block = "\n".join(
                    lines[i:i + size]
                )

                key = cls.hash_text(
                    cls.normalize(block)
                )

                if key in seen:

                    i += size
                    removed = True
                    break

            if not removed:

                line = lines[i]

                key = cls.hash_text(
                    cls.normalize(line)
                )

                if key not in seen:

                    result.append(line)
                    seen.add(key)

                i += 1

        return "\n".join(result)

    @classmethod
    def remove_duplicate_blocks(
        cls,
        text: str,
        min_window: int = 3,
        max_window: int = 20
    ) -> str:

        lines = [
            l.strip()
            for l in text.splitlines()
            if l.strip()
        ]

        result = []

        seen = set()

        i = 0

        while i < len(lines):

            matched = False

            for w in range(
                max_window,
                min_window - 1,
                -1
            ):

                if i + w > len(lines):
                    continue

                block = "\n".join(
                    lines[i:i + w]
                )

                key = cls.hash_text(
                    cls.normalize(block)
                )

                if key in seen:

                    i += w
                    matched = True
                    break

            if not matched:

                result.append(lines[i])

                seen.add(
                    cls.hash_text(
                        cls.normalize(lines[i])
                    )
                )

                i += 1

        return "\n".join(result)

    @classmethod
    def remove_consecutive_blocks(
        cls,
        text: str,
        window: int = 10
    ) -> str:

        lines = text.splitlines()

        result = []

        i = 0

        while i < len(lines):

            block = "\n".join(
                lines[i:i + window]
            )

            if len(result) >= window:

                prev = "\n".join(
                    result[-window:]
                )

                if (
                    cls.normalize(block)
                    == cls.normalize(prev)
                ):

                    i += window
                    continue

            result.append(lines[i])

            i += 1

        return "\n".join(result)

    @classmethod
    def clean(
        cls,
        text: str
    ) -> str:

        text = cls.remove_large_duplicate_blocks(text)

        text = cls.remove_duplicate_blocks(text)

        text = cls.remove_consecutive_blocks(text)

        return text.strip()