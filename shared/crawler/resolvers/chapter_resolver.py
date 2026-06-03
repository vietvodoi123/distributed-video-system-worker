from urllib.parse import urljoin

from bs4 import BeautifulSoup


class ChapterResolver:

    def __init__(
        self,
        engine
    ):
        self.engine = engine

    # =====================================
    # HELPERS
    # =====================================

    def clean_content(
        self,
        text: str
    ) -> str:

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            lines.append(line)

        return "\n".join(lines)

    # =====================================
    # TITLE
    # =====================================

    def extract_title(
        self,
        soup: BeautifulSoup,
        css_title: str | None = None
    ) -> str:

        if css_title:

            node = soup.select_one(
                css_title
            )

            if node:

                text = node.get_text(
                    strip=True
                )

                if text:
                    return text

        if soup.title:

            text = soup.title.get_text(
                strip=True
            )

            if text:
                return text

        h1 = soup.find("h1")

        if h1:

            text = h1.get_text(
                strip=True
            )

            if text:
                return text

        return "Unknown Title"

    # =====================================
    # CONTENT
    # =====================================

    def extract_content(
        self,
        soup: BeautifulSoup,
        css_content: str | None = None
    ) -> str:

        selectors = []

        if css_content:
            selectors.append(
                css_content
            )

        selectors.extend([

            "#chaptercontent",

            ".chapter-content",

            "#content",

            ".content",

            "article"
        ])

        for selector in selectors:

            try:

                node = soup.select_one(
                    selector
                )

            except Exception:
                continue

            if not node:
                continue

            text = node.get_text(
                separator="\n"
            )

            text = self.clean_content(
                text
            )

            if text:
                return text

        return self.clean_content(

            soup.get_text(
                separator="\n"
            )
        )

    # =====================================
    # MAIN
    # =====================================

    async def get_chapter(
        self,
        url: str,
        proxy: str | None = None,
        css_title: str | None = None,
        css_content: str | None = None,
        css_next: str | None = None,
    ) -> dict:

        current_url = url

        html_parts = []

        text_parts = []

        title = None

        visited = set()

        while current_url:

            if current_url in visited:
                break

            visited.add(
                current_url
            )

            html = await self.engine.get_html(

                current_url,

                proxy=proxy
            )

            soup = BeautifulSoup(

                html,

                "html.parser"
            )

            # ==============================
            # TITLE
            # ==============================

            if not title:

                title = self.extract_title(

                    soup,

                    css_title=
                    css_title
                )

            # ==============================
            # CONTENT
            # ==============================

            content = self.extract_content(

                soup,

                css_content=
                css_content
            )

            if content:

                text_parts.append(
                    content
                )

            html_parts.append(
                html
            )

            # ==============================
            # NO PAGINATION CONFIG
            # ==============================

            if not css_next:
                break

            # ==============================
            # NEXT PAGE
            # ==============================

            next_link = soup.select_one(
                css_next
            )

            if not next_link:
                break

            href = next_link.get(
                "href"
            )

            if not href:
                break

            next_url = urljoin(
                current_url,
                href
            )

            if next_url in visited:
                break

            current_url = next_url

        return {

            "title":
            title or "Unknown Title",

            "content":
            "\n\n".join(
                text_parts
            ),

            "html":
            "\n".join(
                html_parts
            )
        }