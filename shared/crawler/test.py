import asyncio
import argparse
from pathlib import Path

from playwright.async_api import async_playwright


DEFAULT_URL = "https://ttks.tw/novel/chapters/congpochanchuancaiguankaishi/index.html"


async def test_url(
    url: str,
    output_path: str | None = None,
    timeout_ms: int = 30000,
) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"URL: {url}")
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            if response is None:
                print("Không nhận được HTTP response (có thể là URL điều hướng nội bộ).")
            else:
                print(f"HTTP status: {response.status}")
                print(f"Final URL: {response.url}")
                print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")

            # Lấy HTML do trình duyệt dựng và nội dung văn bản hiển thị.
            html = await page.content()
            text = await page.locator("body").inner_text()

            print(f"Page title: {await page.title()}")
            print(f"HTML length: {len(html)} characters")
            print(f"Text length: {len(text)} characters")

            print("\n===== TEXT PREVIEW (first 3000 chars) =====")
            print(text[:3000] if text else "(Trang không có văn bản body)")

            if output_path:
                output = Path(output_path)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(html, encoding="utf-8")
                print(f"\nĐã lưu HTML vào: {output.resolve()}")

        finally:
            await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kiểm tra một URL bằng Playwright Chromium headless=True."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_URL,
        help=f"URL cần kiểm tra (mặc định: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="playwright_test_output.html",
        help="Đường dẫn lưu HTML (mặc định: playwright_test_output.html)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout tính bằng mili giây (mặc định: 30000)",
    )
    args = parser.parse_args()

    asyncio.run(
        test_url(
            url=args.url,
            output_path=args.output,
            timeout_ms=args.timeout,
        )
    )


if __name__ == "__main__":
    main()