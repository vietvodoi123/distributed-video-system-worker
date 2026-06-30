import re

from shared.runtime.executors.translation.models.post_process_result import (
    PostProcessAction,
    PostProcessResult,
)


class TranslationPostProcessor:

    MAX_NORMALIZE_PASSES = 10
    MIN_LENGTH_RATIO = 0.35

    MIN_PARAGRAPH_RATIO = 0.40

    def process(
        self,
        *,
        source_text: str,
        translated_text: str,
    ) -> PostProcessResult:

        text = translated_text.strip()

        for _ in range(self.MAX_NORMALIZE_PASSES):

            changed = False

            # ----------------------------------
            # Markdown
            # ----------------------------------

            new_text = self._normalize_markdown(text)

            if new_text != text:
                text = new_text
                changed = True

            # ----------------------------------
            # Prompt Leak
            # ----------------------------------

            new_text = self._normalize_prompt_leak(text)

            if new_text != text:
                text = new_text
                changed = True

            # ----------------------------------
            # Empty
            # ----------------------------------

            if self._is_empty(text):
                return PostProcessResult(
                    action=PostProcessAction.RETRY,
                    text=text,
                    reason="Empty translation.",
                )

            # ----------------------------------
            # Chinese Ratio
            # ----------------------------------

            if self._too_many_chinese(text):
                return PostProcessResult(
                    action=PostProcessAction.RETRY,
                    text=text,
                    reason="Too many Chinese characters.",
                )

            # ----------------------------------
            # Incomplete Translation
            # ----------------------------------

            if self._is_incomplete_translation(
                    source_text,
                    text,
            ):
                return PostProcessResult(
                    action=PostProcessAction.RETRY,
                    text=text,
                    reason="Incomplete translation.",
                )

            # ----------------------------------

            if not changed:

                return PostProcessResult(
                    action=PostProcessAction.ACCEPT,
                    text=text,
                )

        return PostProcessResult(
            action=PostProcessAction.RETRY,
            text=text,
            reason="Normalize loop exceeded.",
        )

    # ======================================================

    @staticmethod
    def _normalize_markdown(
        text: str,
    ) -> str:

        text = re.sub(
            r"^```[\w-]*",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"```$",
            "",
            text,
            flags=re.MULTILINE,
        )

        return text.strip()

    @staticmethod
    def _normalize_prompt_leak(
        text: str,
    ) -> str:

        prefixes = [

            "Bản dịch:",

            "Đây là bản dịch:",

            "Translation:",

            "Here is the translation:",

            "Sure!",

            "Dĩ nhiên!",

        ]

        for prefix in prefixes:

            if text.startswith(prefix):

                return text[len(prefix):].strip()

        return text

    @staticmethod
    def _is_empty(
        text: str,
    ) -> bool:

        return len(text.strip()) == 0

    @staticmethod
    def _too_many_chinese(
        text: str,
    ) -> bool:

        chinese = len(
            re.findall(
                r"[\u4e00-\u9fff]",
                text,
            )
        )

        if chinese == 0:
            return False

        ratio = chinese / len(text)

        return ratio > 0.3

    @staticmethod
    def _length_ratio(
            source: str,
            target: str,
    ) -> float:

        if not source:
            return 1.0

        return len(target) / len(source)

    @staticmethod
    def _paragraph_ratio(
            source: str,
            target: str,
    ) -> float:

        source_count = TranslationPostProcessor._paragraph_count(
            source,
        )

        target_count = TranslationPostProcessor._paragraph_count(
            target,
        )

        if source_count == 0:
            return 1.0

        return target_count / source_count

    @staticmethod
    def _paragraph_count(
            text: str,
    ) -> int:

        paragraphs = [

            line

            for line in text.splitlines()

            if line.strip()

        ]

        return len(paragraphs)

    @classmethod
    def _is_incomplete_translation(
            cls,
            source: str,
            target: str,
    ) -> bool:
        # print(source)
        # print(target)
        if len(source) < 50:
            return False

        length_ratio = cls._length_ratio(
            source,
            target,
        )

        if length_ratio < cls.MIN_LENGTH_RATIO:
            return True

        paragraph_ratio = cls._paragraph_ratio(
            source,
            target,
        )

        if paragraph_ratio < cls.MIN_PARAGRAPH_RATIO:
            return True

        return False