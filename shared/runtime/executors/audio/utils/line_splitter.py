from dataclasses import dataclass


@dataclass
class ScriptLine:

    line_index: int

    text: str


def split_script_lines(
    text: str
) -> list[ScriptLine]:

    results = []

    raw_lines = text.splitlines()

    cleaned_lines = []

    for line in raw_lines:

        cleaned = line.strip()

        if not cleaned:
            continue

        cleaned_lines.append(cleaned)

    for idx, line in enumerate(cleaned_lines):

        results.append(
            ScriptLine(
                line_index=idx,
                text=line
            )
        )

    return results