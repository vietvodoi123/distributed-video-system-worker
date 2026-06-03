import re

from shared.text.cleaners.cn_patterns import (
    AD_PATTERNS,
    NOISE_PATTERNS
)


def clean_cn_content(
    raw_text: str
) -> str:

    text = raw_text.strip()

    # =====================================
    # REMOVE ADS
    # =====================================

    for pattern in AD_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.M
        )

    # =====================================
    # REMOVE NOISE
    # =====================================

    for pattern in NOISE_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.M
        )

    # =====================================
    # NORMALIZE
    # =====================================

    text = text.replace(
        "\u3000",
        " "
    )

    text = text.replace(
        "\xa0",
        " "
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # =====================================
    # COLLAPSE SPACES
    # =====================================

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # =====================================
    # COLLAPSE EMPTY LINES
    # =====================================

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    # =====================================
    # CLEAN LINE BY LINE
    # =====================================

    cleaned_lines = []

    seen = set()

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line in seen:
            continue

        seen.add(line)

        cleaned_lines.append(line)

    return "\n\n".join(
        cleaned_lines
    ).strip()