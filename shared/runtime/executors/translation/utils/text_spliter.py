# shared/runtime/executors/translation/utils/text_splitter.py

class TextSplitter:

    @staticmethod
    def split_by_lines(
        text: str,
        max_chars: int = 8000
    ) -> list[str]:

        lines = [
            line.rstrip()
            for line in text.splitlines()
            if line.strip()
        ]

        chunks = []

        current_chunk = []
        current_length = 0

        for line in lines:

            line_length = len(line) + 1

            if (
                current_length + line_length
                > max_chars
            ):

                chunks.append(
                    "\n".join(current_chunk)
                )

                current_chunk = [line]
                current_length = line_length

            else:

                current_chunk.append(line)
                current_length += line_length

        if current_chunk:

            chunks.append(
                "\n".join(current_chunk)
            )

        return chunks