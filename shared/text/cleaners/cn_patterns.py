# shared/text/cleaners/cn_patterns.py


# ============================================================
# AD / WEBSITE / CRAWLER NOISE
# ============================================================

AD_PATTERNS = [

    # 小说站常见结尾
    r"^喜欢[^。\n]*?请大家收藏：?\([^)]*\)[^。\n]*?更新速度全网最快。?$",

    r"^请收藏本站[:：].*$",
    r"^请收藏本页[:：].*$",

    r"^笔趣阁.*$",
    r"^书海阁小说网.*$",
    r"^这章没有结束，请点击下一页继续阅读！$",

    r"^.*觀看最快的章節更新.*$",
    r"^.*记住本站域名.*$",
    r"^.*記住本站域名.*$",
    r"^.*望讀者記一下我們域名.*$",

    r"^.*請用戶直接瀏覽器訪問.*$",

    r"^最新网址.*$",
    r"^.*最新网址.*$",

    r"^请收藏本站.*$",
    r"^手机用户请.*$",
    r"^本章未完.*$",

    r"^（本章完）$",
    r"^\(本章完\)$",

    r"^chaptererror\(\);$",

    r"^『加入书签.*$",

    r"^天才一秒记住.*$",
    r"^可樂小說.*$",
    r"^天天看小說.*$",
    r"^記住本站.*$",
    r"^最新章節.*$",
    r"^首發.*$",
    r"^本書.*$",

    r"^添加書籤.*$",
    r"^返回目錄.*$",
    r"^章節報錯.*$",
    r"^分享給朋友：.*$",

    # Vietnamese crawler noise nếu chẳng may lọt vào
    r"^Người đăng：?.*$",
    r"^Người đăng:?.*$",
]


# ============================================================
# NOISE
# ============================================================

NOISE_PATTERNS = [

    # dot / ellipsis noise
    r"·\s*·\s*·\s*·",
    r"·······",
    r"\.{3,}",
    r"…{2,}",

    # horizontal separators
    r"[—\-]{3,}",
    r"[—]{5,}",
    r"[─]{5,}",

    # tilde noise
    r"~+",

    # empty brackets
    r"【\s*】",
]


# ============================================================
# DOMAIN / URL
# ============================================================

# URL hoàn chỉnh:
# http://example.com
# https://example.com/abc
# www.example.com
URL_PATTERNS = [

    r"(?i)\bhttps?://[^\s<>\[\]{}\"'，。！？；：、）)】》]+",

    r"(?i)\bwww\.[^\s<>\[\]{}\"'，。！？；：、）)】》]+",
]


# Domain không có http/www:
#
# example.com
# m.shuhaige.net
# abc.cc
# foo.com.cn
#
# Không bắt mọi dấu "." để tránh xóa nhầm nội dung tiếng Trung.
DOMAIN_PATTERN = (
    r"(?i)"
    r"\b"
    r"(?:"
        r"[a-z0-9]"
        r"(?:[a-z0-9-]{0,61}[a-z0-9])?"
        r"\."
    r")+"
    r"(?:"
        r"com|net|org|edu|gov|mil|"
        r"cn|com\.cn|net\.cn|org\.cn|"
        r"cc|co|me|tv|io|ai|"
        r"xyz|top|vip|site|online|"
        r"info|biz|club|pro|app|"
        r"live|store|tech|cloud|"
        r"icu|link|work|win|"
        r"fun|click|shop|"
        r"pw|tk|ga|cf|ml"
    r")"
    r"(?:"
        r":[0-9]{1,5}"
    r")?"
    r"(?:"
        r"/[^\s<>\[\]{}\"'，。！？；：、）)】》]*"
    r")?"
)


# ============================================================
# SENTENCE / LINE BREAK
# ============================================================

# Dấu kết câu thực sự.
#
# 。 ！ ？ ；
# ! ? ;
# 以及 các dạng full-width.
SENTENCE_END_CHARS = (
    "。！？；"
    "!?;"
)


# Dấu có thể dùng để cắt câu dài.
#
# Ưu tiên các dấu mạnh trước, dấu phẩy cuối cùng.
SPLIT_CHARS = (
    "，,、：:"
    "；;"
    "。！？!?"
)


# Dấu phẩy được dùng làm điểm cắt mềm khi
# một câu đã vượt MAX_SENTENCE_LENGTH.
SOFT_SPLIT_CHARS = (
    "，,"
)