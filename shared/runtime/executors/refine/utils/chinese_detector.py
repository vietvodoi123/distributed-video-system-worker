import re


class ChineseDetector:

    CHINESE_PATTERN = re.compile(
        r'[\u4e00-\u9fff]'
    )

    @classmethod
    def has_chinese(
        cls,
        text: str
    ) -> bool:

        return bool(
            cls.CHINESE_PATTERN.search(
                text
            )
        )