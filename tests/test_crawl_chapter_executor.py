import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from shared.runtime.executors.crawl.crawl_chapter_executor import CrawlChapterExecutor


class FakeApiClient:
    def __init__(self):
        self.updates = []

    async def update_chapter_text(self, *, chapter_id: str, data: dict):
        self.updates.append((chapter_id, data))
        return {"ok": True}


def _make_task(payload: dict, chapter_id: str = "chap-100", chapter_number: int = 1):
    return SimpleNamespace(
        id="task-crawl-1",
        task_type="crawl_chapter",
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        payload=payload,
    )


def _make_context(api_client: FakeApiClient, chapter_id: str = "chap-100", chapter_number: int = 1):
    return SimpleNamespace(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        api_client=api_client,
    )


class CrawlChapterExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_crawl_chapter_cleans_spam_with_spam_cleaner(self):
        cn_body = (
            "柳天雄身上恐怖的靈力涌動，逼迫的柳如煙，柳飛龍兩人，齊齊後退到了三米開外。\n"
            "⑻ЬＯOｋ．соｍ\n"
            "長老們肅然而立，大殿內一片寂靜，掌門真人緩緩開口說道今日之事非同小可。\n"
            "【記住本站域名 天天看小說體驗佳，ttt.tw超讚 】\n"
            "轟！仙門納新，測靈根，入選者賞銀五十兩。"
        )
        fake_resp = MagicMock()
        fake_resp.json.return_value = {
            "chaptername": "第一章 宗門大會",
            "txt": cn_body,
        }
        fake_resp.raise_for_status.return_value = None

        api_client = FakeApiClient()
        executor = CrawlChapterExecutor()
        task = _make_task(
            {
                "source_url": "https://example.com/chapter/1",
                "engine": "http",
            }
        )
        ctx = _make_context(api_client)

        with patch("shared.runtime.executors.crawl.crawl_chapter_executor.asyncio.sleep", new=AsyncMock()):
            with patch("shared.runtime.executors.crawl.crawl_chapter_executor.requests.get", return_value=fake_resp):
                result = await executor.execute(task, ctx)

        self.assertEqual(len(api_client.updates), 1)
        chapter_id, update_data = api_client.updates[0]
        self.assertEqual(chapter_id, "chap-100")

        # Spam cleaner should have removed ads
        cleaned = update_data["cleaned_text"]
        self.assertNotIn("⑻ЬＯOｋ．соｍ", cleaned)
        self.assertNotIn("天天看小說", cleaned)
        self.assertIn("柳天雄身上恐怖的靈力涌動", cleaned)
        self.assertIn("第一章 宗門大會", cleaned)

        self.assertEqual(result["result"]["title"], "第一章 宗門大會")


if __name__ == "__main__":
    unittest.main()
