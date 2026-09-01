# shared/text/cleaners/cn_cleaner.py

import re

from shared.text.cleaners.cn_patterns import (
    AD_PATTERNS,
    NOISE_PATTERNS,
    URL_PATTERNS,
    DOMAIN_PATTERN,
    SENTENCE_END_CHARS,
    SOFT_SPLIT_CHARS,
)


# ============================================================
# CONFIG
# ============================================================

# Câu <= giá trị này sẽ không bị tách thêm.
#
# Đây là ngưỡng để tối ưu cho text trước khi đưa sang
# bước dịch / TTS.
MAX_SENTENCE_LENGTH = 110


# Nếu câu vượt MAX_SENTENCE_LENGTH,
# cho phép tìm điểm ngắt trong khoảng này.
#
# Ví dụ:
#
# MAX = 80
# LONG_SENTENCE_LOOKBACK = 30
#
# sẽ tìm dấu phẩy từ vị trí 50 -> 80.
LONG_SENTENCE_LOOKBACK = 40


# Không bao giờ tạo fragment quá ngắn chỉ vì tách câu.
#
# Ví dụ:
#
# "他想，"
#
# không nên bị tách thành:
#
# "他想"
# "，"
MIN_FRAGMENT_LENGTH = 25


# ============================================================
# DOMAIN / URL
# ============================================================

def _remove_urls(text: str) -> str:
    """
    Xóa URL hoàn chỉnh.
    """

    for pattern in URL_PATTERNS:
        text = re.sub(
            pattern,
            "",
            text,
        )

    return text


def _remove_domains(text: str) -> str:
    """
    Xóa domain nằm trong nội dung.

    Ví dụ:

        https://example.com
        http://example.com/a
        www.example.com
        example.com
        m.shuhaige.net

    """

    text = _remove_urls(text)

    text = re.sub(
        DOMAIN_PATTERN,
        "",
        text,
    )

    return text


# ============================================================
# ADS
# ============================================================

def _remove_ads(text: str) -> str:
    """
    Xóa các dòng quảng cáo / crawler noise.
    """

    for pattern in AD_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.M,
        )

    return text


# ============================================================
# NOISE
# ============================================================

def _remove_noise(text: str) -> str:
    """
    Xóa các ký tự noise không mang nội dung.
    """

    for pattern in NOISE_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
        )

    return text


# ============================================================
# NORMALIZE
# ============================================================

def _normalize_text(text: str) -> str:
    """
    Chuẩn hóa whitespace và line ending.
    """

    # Full-width space
    text = text.replace(
        "\u3000",
        " ",
    )

    # Non-breaking space
    text = text.replace(
        "\xa0",
        " ",
    )

    # Windows / old Mac line endings
    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    # Tab -> space
    text = text.replace(
        "\t",
        " ",
    )

    # Collapse spaces
    text = re.sub(
        r"[ ]+",
        " ",
        text,
    )

    # Remove spaces around Chinese punctuation.
    #
    # Ví dụ:
    #
    # "你好 ， 世界 。"
    #
    # -> "你好，世界。"
    text = re.sub(
        r"\s+([，。！？；：、》」』）】])",
        r"\1",
        text,
    )

    text = re.sub(
        r"([（「『【《])\s+",
        r"\1",
        text,
    )

    # Quá nhiều newline
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# EMPTY PUNCTUATION LEFT BY DOMAIN REMOVAL
# ============================================================

def _cleanup_after_domain_removal(text: str) -> str:
    """
    Domain thường nằm trong:

        (m.example.com)

        【www.example.com】

        [example.com]

    Sau khi xóa domain có thể còn:

        ()

        【】

        []

    Hàm này dọn phần còn lại.
    """

    text = re.sub(
        r"\(\s*\)",
        "",
        text,
    )

    text = re.sub(
        r"（\s*）",
        "",
        text,
    )

    text = re.sub(
        r"\[\s*\]",
        "",
        text,
    )

    text = re.sub(
        r"【\s*】",
        "",
        text,
    )

    text = re.sub(
        r"「\s*」",
        "",
        text,
    )

    return text


# ============================================================
# SENTENCE SPLITTER
# ============================================================

def _is_sentence_end(char: str) -> bool:
    return char in SENTENCE_END_CHARS


def _find_soft_break(
    sentence: str,
    start: int,
    max_length: int,
) -> int | None:
    """
    Tìm vị trí cắt mềm cho một câu quá dài.

    Chỉ tìm dấu phẩy trong vùng gần MAX_LENGTH.

    Ví dụ:

        MAX = 80
        LOOKBACK = 30

    sẽ tìm dấu phẩy trong:

        50 -> 80

    Mục tiêu là giữ fragment đủ dài,
    không cắt quá sớm.
    """

    target = min(
        start + max_length,
        len(sentence),
    )

    lower_bound = max(
        start + MIN_FRAGMENT_LENGTH,
        target - LONG_SENTENCE_LOOKBACK,
    )

    # Ưu tiên dấu phẩy gần target nhất.
    for index in range(
        target - 1,
        lower_bound - 1,
        -1,
    ):

        if sentence[index] in SOFT_SPLIT_CHARS:
            return index + 1

    return None


def _split_long_sentence(
    sentence: str,
    max_length: int,
) -> list[str]:
    """
    Tách một câu dài thành các fragment.

    Quan trọng:

    - Không cắt giữa ký tự.
    - Ưu tiên dấu phẩy.
    - Không cắt nếu câu chưa vượt ngưỡng.
    - Không tạo fragment quá ngắn.
    """

    sentence = sentence.strip()

    if not sentence:
        return []

    if len(sentence) <= max_length:
        return [sentence]

    result = []

    start = 0
    length = len(sentence)

    while start < length:

        remaining = length - start

        if remaining <= max_length:
            fragment = sentence[start:].strip()

            if fragment:
                result.append(fragment)

            break

        break_position = _find_soft_break(
            sentence,
            start,
            max_length,
        )

        if break_position is None:
            # Không có dấu phẩy phù hợp.
            #
            # Không cắt giữa chữ.
            # Giữ nguyên câu còn lại.
            fragment = sentence[start:].strip()

            if fragment:
                result.append(fragment)

            break

        fragment = sentence[
            start:break_position
        ].strip()

        if fragment:
            result.append(fragment)

        start = break_position

    return result


def _split_sentences(text: str) -> list[str]:
    """
    Tách toàn bộ text thành các câu.

    Trước tiên tách theo dấu kết câu.
    Sau đó mới xử lý các câu quá dài.
    """

    sentences = []

    current = []

    for char in text:

        current.append(char)

        if _is_sentence_end(char):

            sentence = "".join(current).strip()

            if sentence:
                sentences.append(sentence)

            current = []

    # Phần còn lại không có dấu kết câu
    if current:

        sentence = "".join(current).strip()

        if sentence:
            sentences.append(sentence)

    return sentences


def _split_for_output(text: str) -> list[str]:
    """
    Pipeline tách dòng:

        paragraph
            ↓
        sentence
            ↓
        long sentence
            ↓
        output lines
    """

    base_sentences = _split_sentences(text)

    result = []

    for sentence in base_sentences:

        parts = _split_long_sentence(
            sentence,
            MAX_SENTENCE_LENGTH,
        )

        result.extend(parts)

    return result


# ============================================================
# PARAGRAPH / LINE PROCESSING
# ============================================================

def _process_paragraph(paragraph: str) -> str:
    """
    Xử lý một paragraph độc lập.
    """

    paragraph = paragraph.strip()

    if not paragraph:
        return ""

    lines = _split_for_output(
        paragraph,
    )

    return "\n".join(
        line.strip()
        for line in lines
        if line.strip()
    )


# ============================================================
# MAIN CLEANER
# ============================================================

def clean_cn_content(
    raw_text: str,
) -> str:
    """
    Clean toàn bộ text tiếng Trung.

    Input:
        Toàn bộ raw chapter.

    Output:
        Chinese text đã:

        1. Xóa quảng cáo.
        2. Xóa URL.
        3. Xóa domain.
        4. Xóa noise.
        5. Normalize whitespace.
        6. Tách câu theo dấu kết câu.
        7. Nếu câu quá dài thì tìm dấu phẩy
           gần ngưỡng để tách.
        8. Giữ paragraph / chapter structure.

    Ví dụ:

        result = clean_cn_content(raw_text)
    """

    if not raw_text:
        return ""

    text = raw_text.strip()

    # ========================================================
    # REMOVE ADS
    # ========================================================

    text = _remove_ads(text)

    # ========================================================
    # REMOVE URL / DOMAIN
    # ========================================================

    text = _remove_domains(text)

    # ========================================================
    # REMOVE NOISE
    # ========================================================

    text = _remove_noise(text)

    # ========================================================
    # CLEAN LEFTOVER PUNCTUATION
    # ========================================================

    text = _cleanup_after_domain_removal(text)

    # ========================================================
    # NORMALIZE
    # ========================================================

    text = _normalize_text(text)

    if not text:
        return ""

    # ========================================================
    # PROCESS PARAGRAPHS
    # ========================================================

    paragraphs = []

    for paragraph in re.split(
        r"\n\s*\n+",
        text,
    ):

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        processed = _process_paragraph(
            paragraph,
        )

        if processed:
            paragraphs.append(
                processed,
            )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    result = "\n\n".join(
        paragraphs,
    )

    return result.strip()