import re


MAX_TITLE_LENGTH = 40


def clean_chapter_title(
    title: str,
    chapter_number: int | None = None,
    max_length: int = MAX_TITLE_LENGTH
) -> str:

    if not title:
        return ""

    text = str(title).strip()

    # =========================
    # Xóa nội dung trong ngoặc
    # =========================

    patterns = [

        r"\([^)]*\)",      # (...)
        r"（[^）]*）",      # （...）
        r"\[[^\]]*\]",     # [...]
        r"【[^】]*】",      # 【...】
        r"《[^》]*》",      # 《...》
        r"「[^」]*」",      # 「...」
        r"『[^』]*』",      # 『...』
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            "",
            text
        )

    # =========================
    # Xóa tiền tố chương
    # =========================

    prefix_patterns = [

        # 第2253章 xxx
        r"^\s*第\s*\d+\s*章\s*[:：\-—、,.，]?\s*",

        # Thứ 2253 chương xxx
        r"^\s*Thứ\s*\d+\s*chương\s*[:：\-—、,.，]?\s*",

        # Chương 2253 xxx
        r"^\s*Chương\s*\d+\s*[:：\-—、,.，]?\s*",

        # 2253: xxx
        r"^\s*\d+\s*[:：\-—、,.，]+\s*",
    ]

    for pattern in prefix_patterns:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    # =========================
    # Nếu biết chapter_number
    # thì xóa chính xác hơn
    # =========================

    if chapter_number is not None:

        text = re.sub(

            rf"^\s*第\s*{chapter_number}\s*章\s*",

            "",

            text,

            flags=re.IGNORECASE
        )

        text = re.sub(

            rf"^\s*Thứ\s*{chapter_number}\s*chương\s*",

            "",

            text,

            flags=re.IGNORECASE
        )

        text = re.sub(

            rf"^\s*Chương\s*{chapter_number}\s*",

            "",

            text,

            flags=re.IGNORECASE
        )

    # =========================
    # Xóa ký tự đầu thừa
    # =========================

    text = re.sub(

        r"^[\s\-—:：、,.，]+",

        "",

        text
    )

    # =========================
    # Chuẩn hóa khoảng trắng
    # =========================

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    # =========================
    # Giới hạn độ dài
    # =========================

    if len(text) > max_length:

        text = (
            text[:max_length]
            .rstrip()
            + "..."
        )

    return text