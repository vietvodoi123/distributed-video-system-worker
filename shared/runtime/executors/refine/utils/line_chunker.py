class LineChunker:

    @staticmethod
    def chunk_by_lines(
        text: str,
        max_lines: int = 15
    ) -> list[str]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        chunks = []

        current_chunk = []

        for line in lines:

            current_chunk.append(line)

            if len(current_chunk) >= max_lines:

                chunks.append(
                    "\n".join(current_chunk)
                )

                current_chunk = []

        if current_chunk:

            chunks.append(
                "\n".join(current_chunk)
            )

        return chunks