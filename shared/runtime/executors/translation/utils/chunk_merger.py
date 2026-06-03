# shared/runtime/executors/translation/utils/chunk_merger.py

import re


class ChunkMerger:

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
    def get_overlap(
        cls,
        a: str,
        b: str,
        min_len: int = 100
    ) -> int:

        a_norm = cls.normalize(a)
        b_norm = cls.normalize(b)

        max_len = min(
            len(a_norm),
            len(b_norm)
        )

        for i in range(
            max_len,
            min_len,
            -1
        ):

            if (
                a_norm[-i:]
                == b_norm[:i]
            ):

                return i

        return 0

    @classmethod
    def merge_smart(
        cls,
        chunks: list[str]
    ) -> str:

        if not chunks:
            return ""

        result = chunks[0]

        for nxt in chunks[1:]:

            overlap = cls.get_overlap(
                result,
                nxt
            )

            if overlap > 0:
                nxt = nxt[overlap:]

            result += "\n" + nxt

        return result.strip()