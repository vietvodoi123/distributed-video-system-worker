import re
import unicodedata

HOMOGLYPH_MAP = str.maketrans({
    "а": "a", "А": "A",
    "в": "b", "В": "B",
    "с": "c", "С": "C",
    "е": "e", "Е": "E",
    "н": "h", "Н": "H",
    "і": "i", "І": "I",
    "ј": "j", "Ј": "J",
    "к": "k", "К": "K",
    "м": "m", "М": "M",
    "о": "o", "О": "O", "Ο": "O", "ο": "o",
    "р": "p", "Р": "P", "Ρ": "P", "ρ": "p",
    "т": "t", "Т": "T", "Τ": "T",
    "х": "x", "Х": "X", "Χ": "X",
    "у": "y", "У": "Y", "Υ": "Y",
    "α": "a", "Α": "A",
    "β": "b", "Β": "B",
    "ε": "e", "Ε": "E",
    "κ": "k", "Κ": "K",
    "ν": "v", "Ν": "N",
    "з": "3", "З": "3",
    "ѕ": "s", "Ѕ": "S",
    "υ": "u", "Υ": "U",
    "ɩ": "i", "ǐ": "i", "í": "i", "é": "e",
    "ж": "x", "Ж": "X",
    "ร": "r", "๓": "m", "א": "x",
    "。": ".", "．": ".", "·": ".", "•": ".",
})

CHAPTER_HEADING_RE = re.compile(
    r"^(?:第\s*[0-9一二三四五六七八九十百千万两零]+\s*[章回节卷集]|\d{1,5}\s+[\u4e00-\u9fff])"
)

STANDARD_CJK_FULLWIDTH_PUNCT = set("，。！？：；（）「」『』《》【】～、—…·．")


def is_cjk(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def normalize_for_model(text: str) -> str:
    """Normalize NFKC (fancy math/circled fonts -> ASCII) and map homoglyphs."""
    nfkc = unicodedata.normalize("NFKC", text)
    mapped = nfkc.translate(HOMOGLYPH_MAP)
    return " ".join(mapped.split()).lower()


def is_chapter_heading(text: str, pos_ratio: float) -> float:
    if pos_ratio <= 0.03 and CHAPTER_HEADING_RE.match(text.strip()) and len(text.strip()) <= 45:
        return 1.0
    return 0.0


def extract_unicode_script_features(text: str) -> list[float]:
    """
    Domain-agnostic Unicode script distribution features.
    Detects fancy math fonts, circled chars, Cyrillic/Greek/Thai/Hebrew lookalikes,
    emojis/dingbats, and dot-separated obfuscated strings without domain regexes.
    """
    if not text:
        return [0.0] * 7

    length = len(text)
    cjk_cnt = 0
    ascii_alnum_cnt = 0
    fancy_nfkc_cnt = 0
    foreign_alpha_cnt = 0
    symbol_emoji_cnt = 0
    dot_cnt = 0

    for ch in text:
        if is_cjk(ch):
            cjk_cnt += 1
            continue

        nfkc_ch = unicodedata.normalize("NFKC", ch)
        if nfkc_ch != ch and ch not in STANDARD_CJK_FULLWIDTH_PUNCT:
            fancy_nfkc_cnt += 1

        if ch.isascii() and ch.isalnum():
            ascii_alnum_cnt += 1
        elif ch.isalpha():
            foreign_alpha_cnt += 1

        cat = unicodedata.category(ch)
        if cat in ("So", "Sm", "Sk") and ch not in STANDARD_CJK_FULLWIDTH_PUNCT:
            symbol_emoji_cnt += 1

        if ch in (".", "。", "．", "·", "•"):
            dot_cnt += 1

    return [
        min(length / 120.0, 2.0),
        cjk_cnt / length,
        ascii_alnum_cnt / length,
        fancy_nfkc_cnt / length,
        foreign_alpha_cnt / length,
        symbol_emoji_cnt / length,
        dot_cnt / length,
    ]


def split_cjk_tail(text: str) -> tuple[str, str, str]:
    """
    Split a line into (story_prefix_including_punct, tail_after_cjk, trailing_quote).
    Example: '「你好。💜 69shux.com」' -> ('「你好。', '💜 69shux.com', '」')
    """
    work = text.rstrip()
    trailing_quote = ""
    if work.endswith(("」", "”", "』")) and work.count("「") > work[:-1].count("」"):
        trailing_quote = work[-1]
        work = work[:-1].rstrip()

    last_cjk = -1
    for i in range(len(work) - 1, -1, -1):
        if is_cjk(work[i]):
            has_cjk_neighbor = (i > 0 and is_cjk(work[i - 1])) or (i + 1 < len(work) and is_cjk(work[i + 1]))
            if has_cjk_neighbor or i < len(work) * 0.5:
                last_cjk = i
                break

    if last_cjk == -1:
        return "", text, ""

    cut = last_cjk + 1
    while cut < len(work) and work[cut] in "。！？…，、：；）》」』”～~":
        cut += 1

    prefix = work[:cut].rstrip()
    tail = work[cut:].strip()
    return prefix, tail, trailing_quote


def strip_tail_at_cjk_boundary(text: str) -> str:
    """Called when the ML tail classifier confirms the tail is spam."""
    prefix, _tail, trailing_quote = split_cjk_tail(text)
    if not prefix or len(prefix) <= 3:
        return ""
    return prefix + trailing_quote
