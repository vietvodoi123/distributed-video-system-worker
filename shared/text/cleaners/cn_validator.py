import re
import unicodedata


_CHINESE_RE = re.compile(
    r"[\u3400-\u9FFF]"
)


def validate_raw_text(
    text: str
) -> None:
    """
    Validate dữ liệu vừa crawl.
    Chỉ bắt lỗi encoding/binary.
    """

    if not text or not text.strip():

        raise ValueError(
            "Chapter is empty."
        )


    total = len(text)


    control = sum(
        1
        for ch in text
        if unicodedata.category(ch).startswith("C")
        and ch not in ("\n", "\r", "\t")
    )


    if control / total > 0.10:

        raise ValueError(
            f"Binary corrupted content "
            f"(control={control}/{total})"
        )


    replacement = text.count(
        "\uFFFD"
    )


    if replacement > 50:

        raise ValueError(
            f"Decode failed "
            f"(replacement={replacement})"
        )



def validate_cleaned_chapter(
    text: str
) -> None:


    if not text:

        raise ValueError(
            "Cleaned chapter empty."
        )


    total = len(text)


    chinese = len(
        _CHINESE_RE.findall(
            text
        )
    )


    if total > 300 and chinese < 100:

        raise ValueError(
            f"Too little Chinese content "
            f"(chinese={chinese})"
        )


    ratio = chinese / total


    if total > 500 and ratio < 0.10:

        raise ValueError(
            f"Low Chinese ratio "
            f"{ratio:.2%}"
        )