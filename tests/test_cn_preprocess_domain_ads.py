"""Regression tests for novel text that can break the Reddit renderer."""

import re
import unittest

from shared.text.cleaners.cn_cleaner import clean_cn_content


class ChinesePreprocessRegressionTest(unittest.TestCase):
    def test_removes_domains_and_inline_site_promotions(self):
        raw_text = (
            "两人都露出惊讶之色，互相看了一眼。"
            "（由于缓存原因，请用户直接浏览器访问 追书认准天天看小说，"
            "ttk.tw超便捷网站，观看最快的章节更新）"
            "中阶力士继续向前。\n\n"
            "【记住本站域名 天天看小说书海量，ttk.tw任你挑】"
        )

        cleaned = clean_cn_content(raw_text)

        self.assertNotIn("ttk.tw", cleaned)
        self.assertNotIn("请用户直接浏览器访问", cleaned)
        self.assertNotIn("记住本站域名", cleaned)
        self.assertNotIn("天天看小说", cleaned)
        self.assertIn("两人都露出惊讶之色", cleaned)
        self.assertIn("中阶力士继续向前", cleaned)

    def test_removes_common_and_unicode_domains(self):
        raw_text = (
            "正文开始。example.com、www.example.net、https://foo.org/a，"
            "𝟨𝟫𝐬𝐡𝐮𝐱.𝐜𝐨𝐦 都是站点信息。正文结束。"
        )

        cleaned = clean_cn_content(raw_text)

        self.assertNotRegex(
            cleaned,
            re.compile(r"(?:https?://|www\.)?\S+\.(?:com|net|org)", re.I),
        )
        self.assertNotIn("69shux.com", cleaned)
        self.assertIn("正文开始", cleaned)
        self.assertIn("正文结束", cleaned)

    def test_keeps_mojibake_visible_for_encoding_diagnosis(self):
        """Encoding corruption must be diagnosed by the crawler layer."""
        raw_text = "Hai người đều lộ ra vẻ kinh ngạc. 69s NNx <0xCC><0x87>."

        cleaned = clean_cn_content(raw_text)

        self.assertIn("<0xCC>", cleaned)

    def test_removes_homoglyphs_and_obfuscated_domains(self):
        raw_text = (
            "街角還有個攤子，攤主扯著嗓子喊：“賣白菜，地里剛摘的白菜！”\n"
            "⑧вОΟｋ.Ｃоｍ\n"
            "【記住本站域名 天天看小說體驗佳，𝘵𝘵𝘬.𝘵𝘸超讚 】\n"
            "看書首選天天看小說，𝓽𝓽𝓴.𝓽𝔀超給力\n"
            "（由於緩存原因，請用戶直接瀏覽器訪問 天天看小說超貼心，𝙩𝘵𝙠.𝙩𝙬等你讀 網站，觀看最快的章節更新）\n"
            "⑧bοоК．ｃＯm\n"
            "⒏ｂoОК.CΟｍ\n"
            "他扶著墻走到街頭，發現今天街上特別熱鬧。"
        )

        cleaned = clean_cn_content(raw_text)

        self.assertNotIn("8book.com", cleaned.lower())
        self.assertNotIn("ttk.tw", cleaned.lower())
        self.assertNotIn("天天看小說", cleaned)
        self.assertNotIn("⑧вОΟｋ", cleaned)
        self.assertNotIn("⑧bοоК", cleaned)
        self.assertNotIn("⒏ｂoОК", cleaned)
        self.assertIn("賣白菜，地里剛摘的白菜", cleaned)
        self.assertIn("他扶著墻走到街頭，發現今天街上特別熱鬧", cleaned)

    def test_removes_standalone_ad_line_with_promotional_phrases(self):
        raw_text = (
            "轟！\n\n"
            "   讀小說上天天看小說，𝒕𝒕𝒌.𝒕𝒘超省心\n\n"
            "  柳天雄身上恐怖的靈力涌動，逼迫的柳如煙，柳飛龍兩人，齊齊後退到了三米開外。"
        )

        cleaned = clean_cn_content(raw_text)

        self.assertNotIn("讀小說上天天看小說", cleaned)
        self.assertNotIn("超省心", cleaned)
        self.assertNotIn("ttk.tw", cleaned.lower())
        self.assertIn("轟！", cleaned)
        self.assertIn("柳天雄身上恐怖的靈力涌動", cleaned)
        self.assertIn("齊齊後退到了三米開外", cleaned)

    def test_removes_parenthesized_digit_and_soft_sign_domain(self):
        raw_text = (
            "“叮鈴鈴……”鄭玉龍本想請王野吃飯，結果話還沒說完，手機就響了起來。\n"
            "“爸，怎麼了？”\n"
            "⑻ЬＯOｋ．соｍ\n"
            "“好，我馬上回去。”"
        )

        cleaned = clean_cn_content(raw_text)

        self.assertNotIn("8book", cleaned.lower())
        self.assertNotIn("⑻", cleaned)
        self.assertNotIn("соｍ", cleaned)
        self.assertIn("鄭玉龍本想請王野吃飯", cleaned)
        self.assertIn("爸，怎麼了？", cleaned)
        self.assertIn("好，我馬上回去。", cleaned)


if __name__ == "__main__":
    unittest.main()
