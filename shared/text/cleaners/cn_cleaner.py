# shared/text/cleaners/cn_cleaner.py

import re
import unicodedata

from shared.text.cleaners.cn_patterns import (
    AD_PATTERNS,
    INLINE_AD_PATTERNS,
    NOISE_PATTERNS,
    URL_PATTERNS,
    DOMAIN_PATTERN,
    HOMOGLYPH_MAP,
    SENTENCE_END_CHARS,
    CLOSING_QUOTE_CHARS,
)


# ============================================================
# CONFIG
# ============================================================

# Đây là NGƯỠNG để bắt đầu tìm dấu kết câu.
#
# Không có nghĩa câu sẽ bị cắt đúng tại 110 ký tự.
#
# Ví dụ:
#
# 100 ký tự + dấu 。
# -> giữ nguyên.
#
# 150 ký tự
# -> tìm dấu kết câu tiếp theo sau mốc 110.
#
# 300 ký tự
# -> tiếp tục tìm dấu kết câu.
#
MAX_SENTENCE_LENGTH = 110


# ============================================================
# URL / DOMAIN
# ============================================================

def _remove_urls(
    text: str,
) -> str:
    """
    Xóa URL hoàn chỉnh.

    Ví dụ:

        https://example.com
        http://example.com/abc
        www.example.com
    """

    for pattern in URL_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
        )

    return text


def _remove_domains(
    text: str,
) -> str:
    """
    Xóa URL và domain.

    Ví dụ:

        https://example.com
        www.example.com
        example.com
        m.example.com
    """

    text = _remove_urls(
        text
    )

    # 1. Xóa domain ASCII bình thường.
    text = re.sub(
        DOMAIN_PATTERN,
        "",
        text,
    )

    # 2. Xóa domain bị Unicode hóa / làm giả ký tự.
    #
    # Ví dụ:
    #     𝟨𝟫𝐬𝐡𝐮𝐱.𝐜𝐨𝐦
    #
    # NFKC sẽ biến chuỗi trên thành:
    #     69shux.com
    #
    # Không normalize toàn bộ chapter vì NFKC có thể làm thay đổi
    # các ký tự Unicode khác trong nội dung tiếng Trung.
    text = _remove_unicode_domains(
        text
    )

    return text


def _remove_unicode_domains(
    text: str,
) -> str:
    """
    Xóa domain sử dụng Unicode lookalike / mathematical characters / homoglyphs.

    Chỉ normalize từng candidate có dấu chấm thay vì normalize
    toàn bộ text, để không làm thay đổi nội dung tiếng Trung.

    Ví dụ:
        𝟨𝟫𝐬𝐡𝐮𝐱.𝐜𝐨𝐦 -> 69shux.com -> bị xóa
        ⑧вОΟｋ.Ｃоｍ -> 8book.com -> bị xóa
        ⑧bοоК．ｃＯm -> 8book.com -> bị xóa
        ⒏ｂoОК.CΟｍ -> 8.book.com -> bị xóa
        example.com     -> đã được xử lý bởi DOMAIN_PATTERN
    """

    # Bắt candidate có dấu chấm hoặc ký tự chấm tương đương,
    # không ăn lan sang chữ Hán hoặc dấu câu tiếng Trung.
    candidate_pattern = CANDIDATE_DOMAIN_PATTERN

    def replace_candidate(
        match: re.Match,
    ) -> str:
        candidate = match.group(0)

        normalized = _normalize_confusables(candidate)

        # Sau khi giải mã homoglyphs và NFKC, nếu khớp domain thì xóa
        # candidate GỐC, không xóa bản normalized.
        if re.fullmatch(
            DOMAIN_PATTERN,
            normalized,
            flags=re.IGNORECASE,
        ) or re.search(
            DOMAIN_PATTERN,
            normalized,
            flags=re.IGNORECASE,
        ):
            return ""

        return candidate

    return candidate_pattern.sub(
        replace_candidate,
        text,
    )


# ============================================================
# AD & DOMAIN LINES REMOVAL
# ============================================================

AD_LINE_KEYWORDS = re.compile(
    r"(?:天天看小說|天天看小说|讀小說|读小说|看小說|看小说|看書首選|看书首选|"
    r"追書認準|追书认准|最新網址|最新网址|記住本站|记住本站|本站域名|"
    r"瀏覽器訪問|浏览器访问|觀看最快|观看最快|緩存原因|缓存原因|"
    r"超省心|超給力|超给力|超貼心|超贴心|體驗佳|体验佳|等你讀|等你读|超讚|超赞|等你看|無彈窗|无弹窗)"
)

CANDIDATE_DOMAIN_PATTERN = re.compile(
    r"""(?<![a-zA-Z0-9])[^\s\u4e00-\u9fff\u3400-\u4dbf，。！？；：、（）()【】《》「」『』"'<>\[\]{}]+"""
    r"""[\.．․‧•·]"""
    r"""[^\s\u4e00-\u9fff\u3400-\u4dbf，。！？；：、（）()【】《》「」『』"'<>\[\]{}]+"""
)


def _normalize_confusables(candidate_str: str) -> str:
    # Ánh xạ các ký tự ngoặc đơn/đồng hình trước (như ⑻ -> 8) để tránh bị NFKC tách thành (8)
    t = candidate_str.translate(HOMOGLYPH_MAP)
    t = unicodedata.normalize("NFKC", t)
    return t.translate(HOMOGLYPH_MAP)


def _line_contains_domain(line: str) -> bool:
    for p in URL_PATTERNS:
        if re.search(p, line):
            return True
    if re.search(DOMAIN_PATTERN, line):
        return True
    # Kiểm tra toàn bộ dòng sau khi chuẩn hóa (rất hiệu quả cho dòng tên miền đứng riêng)
    norm_line = _normalize_confusables(line)
    if re.search(DOMAIN_PATTERN, norm_line):
        return True
    for m in CANDIDATE_DOMAIN_PATTERN.finditer(line):
        candidate = m.group(0)
        norm = _normalize_confusables(candidate)
        if re.fullmatch(DOMAIN_PATTERN, norm, flags=re.IGNORECASE) or re.search(DOMAIN_PATTERN, norm, flags=re.IGNORECASE):
            return True
    return False


def _remove_ad_and_domain_lines(text: str) -> str:
    """
    Xóa toàn bộ dòng nếu dòng đó là dòng watermark / quảng cáo:
    - Dòng chứa tên miền + từ khóa quảng cáo (như '讀小說上天天看小說，𝒕𝒕𝒌.𝒕𝒘超省心')
    - Dòng chứa tên miền và ngắn (<= 50 ký tự như '⑧вОΟｋ.Ｃоｍ')
    - Dòng chứa cụm từ quảng cáo đứng riêng (<= 60 ký tự)
    """
    lines = []
    for line in text.splitlines():
        strip_l = line.strip()
        if not strip_l:
            lines.append(line)
            continue
        has_dom = _line_contains_domain(strip_l)
        has_ad = bool(AD_LINE_KEYWORDS.search(strip_l))
        if (has_dom and has_ad and len(strip_l) <= 100) or (has_dom and len(strip_l) <= 50) or (has_ad and len(strip_l) <= 60):
            continue
        lines.append(line)
    return "\n".join(lines)


# ============================================================
# ADS
# ============================================================

def _remove_ads(
    text: str,
) -> str:
    """
    Xóa các dòng quảng cáo / crawler.
    """

    for pattern in AD_PATTERNS:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.M,
        )

    return text


def _remove_inline_ads(
    text: str,
) -> str:
    """Xóa quảng cáo được chèn trong cùng dòng với nội dung truyện."""

    for pattern in INLINE_AD_PATTERNS:
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

def _remove_noise(
    text: str,
) -> str:
    """
    Xóa noise không mang nội dung.
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

def _normalize_text(
    text: str,
) -> str:
    """
    Chuẩn hóa whitespace nhưng không thay đổi
    nội dung tiếng Trung.
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

    # Windows newline
    text = text.replace(
        "\r\n",
        "\n",
    )

    # Old Mac newline
    text = text.replace(
        "\r",
        "\n",
    )

    # Tab -> space
    text = text.replace(
        "\t",
        " ",
    )

    # Collapse multiple spaces
    text = re.sub(
        r"[ ]+",
        " ",
        text,
    )

    # Xóa space trước punctuation.
    text = re.sub(
        r"\s+([，。！？；：、》」』）】〉])",
        r"\1",
        text,
    )

    # Xóa space sau opening bracket.
    text = re.sub(
        r"([（「『【《〈“‘])\s+",
        r"\1",
        text,
    )

    # Không để quá nhiều dòng trống.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# EMPTY BRACKETS
# ============================================================

def _cleanup_after_domain_removal(
    text: str,
) -> str:
    """
    Domain có thể nằm trong:

        (example.com)
        （example.com）
        【example.com】

    Sau khi xóa domain có thể còn ngoặc rỗng.
    """

    empty_pairs = [

        r"\(\s*\)",

        r"（\s*）",

        r"\[\s*\]",

        r"【\s*】",

        r"「\s*」",

        r"『\s*』",
    ]

    for pattern in empty_pairs:

        text = re.sub(
            pattern,
            "",
            text,
        )

    return text


# ============================================================
# SENTENCE END
# ============================================================

def _is_sentence_end(
    char: str,
) -> bool:
    """
    Kiểm tra một ký tự có phải dấu kết câu hay không.
    """

    return char in SENTENCE_END_CHARS


def _get_sentence_end(
    text: str,
    index: int,
) -> int:
    """
    Xác định vị trí kết thúc thực tế của câu.

    Ví dụ:

        你真的要走吗？”

    index đang trỏ vào:

        ？

    thì kết thúc thực tế phải là sau:

        ？”

    """

    position = index + 1

    # Chỉ kiểm tra ký tự LIỀN KỀ.
    #
    # Không parse ngoặc.
    while (
        position < len(text)
        and text[position]
        in CLOSING_QUOTE_CHARS
    ):
        position += 1

    return position


# ============================================================
# SPLIT SENTENCES
# ============================================================

def _split_sentences(
    text: str,
) -> list[str]:
    """
    Tách text thành các câu hoàn chỉnh.

    Quy tắc:

        。！？；!?;
        + dấu đóng ngoặc liền kề

    Ví dụ:

        他说：“你真的要走吗？”
        青阳没有回答。

    Kết quả:

        他说：“你真的要走吗？”
        青阳没有回答。
    """

    sentences = []

    start = 0
    index = 0

    while index < len(text):

        char = text[index]

        if _is_sentence_end(
            char
        ):

            end = _get_sentence_end(
                text,
                index,
            )

            sentence = text[
                start:end
            ].strip()

            if sentence:

                sentences.append(
                    sentence
                )

            start = end
            index = end

            continue

        index += 1

    # Phần cuối không có dấu kết câu.
    if start < len(text):

        sentence = text[
            start:
        ].strip()

        if sentence:

            sentences.append(
                sentence
            )

    return sentences


# ============================================================
# FIND NEXT SENTENCE END
# ============================================================

def _find_next_sentence_end(
    text: str,
    start: int,
) -> int | None:
    """
    Tìm dấu kết câu đầu tiên kể từ start.

    Không tìm dấu phẩy.

    Không cắt giữa câu.
    """

    index = start

    while index < len(text):

        if _is_sentence_end(
            text[index]
        ):

            return _get_sentence_end(
                text,
                index,
            )

        index += 1

    return None


# ============================================================
# SPLIT LONG SENTENCE
# ============================================================

def _split_long_sentence(
    sentence: str,
    max_length: int = MAX_SENTENCE_LENGTH,
) -> list[str]:
    """
    Xử lý câu dài.

    QUY TẮC QUAN TRỌNG:

        Câu <= max_length
            -> giữ nguyên.

        Câu > max_length
            -> KHÔNG tìm dấu phẩy.

        -> tìm dấu kết câu tiếp theo.

        -> xuống dòng sau dấu kết câu.

    Không bao giờ cắt cứng giữa chữ.
    """

    sentence = sentence.strip()

    if not sentence:

        return []

    # --------------------------------------------------------
    # CÂU KHÔNG DÀI
    # --------------------------------------------------------

    if len(sentence) <= max_length:

        return [
            sentence
        ]

    # --------------------------------------------------------
    # CÂU DÀI
    #
    # Ở đây sentence vốn đã là một câu hoàn chỉnh.
    #
    # Vì vậy không có dấu kết câu nào bên trong nữa
    # để tìm.
    #
    # Do đó câu này được giữ nguyên.
    # --------------------------------------------------------

    return [
        sentence
    ]


# ============================================================
# SMART LINE SPLITTER
# ============================================================

def _split_long_text(
    text: str,
    max_length: int = MAX_SENTENCE_LENGTH,
) -> list[str]:
    """
    Đây là hàm thực hiện việc chia dòng.

    Khác với _split_sentences():

        _split_sentences()
        -> tách tại mọi dấu kết câu.

    Hàm này:

        - cho phép một đoạn dài chứa nhiều câu
        - nếu tổng dòng vượt max_length
        - tìm dấu kết câu tiếp theo
        - rồi mới xuống dòng.

    Tuyệt đối không dùng dấu phẩy.
    """

    result = []

    start = 0
    length = len(text)

    while start < length:

        remaining = length - start

        # ----------------------------------------------------
        # Phần còn lại ngắn hơn ngưỡng.
        # ----------------------------------------------------

        if remaining <= max_length:

            fragment = text[
                start:
            ].strip()

            if fragment:

                result.append(
                    fragment
                )

            break

        # ----------------------------------------------------
        # Đã vượt ngưỡng.
        #
        # Tìm dấu kết câu đầu tiên
        # SAU vị trí max_length.
        # ----------------------------------------------------

        search_start = (
            start + max_length
        )

        end = _find_next_sentence_end(
            text,
            search_start,
        )

        # ----------------------------------------------------
        # Không có dấu kết câu nữa.
        #
        # Không cắt cứng.
        # ----------------------------------------------------

        if end is None:

            fragment = text[
                start:
            ].strip()

            if fragment:

                result.append(
                    fragment
                )

            break

        # ----------------------------------------------------
        # Có dấu kết câu.
        # ----------------------------------------------------

        fragment = text[
            start:end
        ].strip()

        if fragment:

            result.append(
                fragment
            )

        start = end

    return result


# ============================================================
# PARAGRAPH
# ============================================================

def _process_paragraph(
    paragraph: str,
) -> str:
    """
    Xử lý một paragraph.
    """

    paragraph = paragraph.strip()

    if not paragraph:

        return ""

    lines = _split_long_text(
        paragraph,
        MAX_SENTENCE_LENGTH,
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
    Entry point duy nhất.

    Chỉ cần truyền toàn bộ Chinese text:

        cleaned = clean_cn_content(raw_text)

    Hàm sẽ:

        1. Xóa quảng cáo.
        2. Xóa URL.
        3. Xóa domain.
        4. Xóa noise.
        5. Normalize whitespace.
        6. Tách dòng theo dấu kết câu.
        7. Với dòng vượt 110 ký tự,
           tìm dấu kết câu tiếp theo.
        8. Nếu dấu kết câu có dấu đóng ngoặc
           ngay sau nó thì lấy luôn dấu đóng ngoặc.
    """

    if not raw_text:

        return ""

    text = raw_text.strip()

    # --------------------------------------------------------
    # REMOVE ADS
    # --------------------------------------------------------

    text = _remove_inline_ads(
        text
    )

    text = _remove_ads(
        text
    )

    # --------------------------------------------------------
    # REMOVE DEDICATED AD & DOMAIN LINES
    # --------------------------------------------------------

    text = _remove_ad_and_domain_lines(
        text
    )

    # --------------------------------------------------------
    # REMOVE URL / DOMAIN
    # --------------------------------------------------------

    text = _remove_domains(
        text
    )

    # --------------------------------------------------------
    # REMOVE NOISE
    # --------------------------------------------------------

    text = _remove_noise(
        text
    )

    # --------------------------------------------------------
    # CLEAN EMPTY BRACKETS
    # --------------------------------------------------------

    text = _cleanup_after_domain_removal(
        text
    )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    text = _normalize_text(
        text
    )

    if not text:

        return ""

    # --------------------------------------------------------
    # PROCESS PARAGRAPHS
    # --------------------------------------------------------

    paragraphs = []

    for paragraph in re.split(
        r"\n\s*\n+",
        text,
    ):

        paragraph = paragraph.strip()

        if not paragraph:

            continue

        processed = _process_paragraph(
            paragraph
        )

        if processed:

            paragraphs.append(
                processed
            )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    return "\n\n".join(
        paragraphs
    ).strip()
