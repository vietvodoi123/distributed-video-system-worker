import re
import unicodedata


_CHINESE_RE = re.compile(r"[\u3400-\u9FFF]")


def validate_chapter_text(text: str) -> None:
    """
    Raise ValueError nếu chapter có dấu hiệu bị hỏng.
    """

    if not text or not text.strip():
        raise ValueError("Chapter is empty.")

    total = len(text)

    # Control characters (trừ \n \r \t)
    control = sum(
        1
        for ch in text
        if unicodedata.category(ch).startswith("C")
        and ch not in ("\n", "\r", "\t")
    )

    if control / total > 0.02:
        raise ValueError(
            f"Chapter appears to contain binary/corrupted data "
            f"(control_chars={control}/{total})."
        )

    replacement = text.count("\uFFFD")

    if replacement > 5:
        raise ValueError(
            "Chapter contains many Unicode replacement characters (�)."
        )

    chinese = len(_CHINESE_RE.findall(text))

    printable = sum(c.isprintable() for c in text)

    if printable > 200 and chinese / printable < 0.03:
        raise ValueError(
            f"Invalid chapter content: "
            f"control={control}/{total}, "
            f"replacement={replacement}, "
            f"chinese_ratio={chinese / max(printable, 1):.2%}"
        )