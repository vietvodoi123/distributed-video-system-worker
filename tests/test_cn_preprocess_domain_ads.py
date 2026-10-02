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


if __name__ == "__main__":
    unittest.main()
