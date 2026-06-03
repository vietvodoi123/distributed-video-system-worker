from urllib.parse import (
    urljoin,
    urlparse,
    unquote
)


def build_txt_url(
    base_url,
    book_id,
    chapter_id,
    secret,
    book_list
):

    secret_str = str(secret)

    start = (
        int(chapter_id) * 3
    ) % 100

    suffix = (
        secret_str[start:start + 5]
    )
    return (
        f"{base_url.rstrip('/')}"
        f"/txt/{book_list}/"
        f"{book_id}/"
        f"{chapter_id}{suffix}.html"
    )


def build_absolute_url(
    base_url: str,
    href: str,
    website=None,
    source_config=None
) -> str:

    if not href:
        return ""

    href = href.strip()

    # =========================
    # SPECIAL CASE: 8BOOK
    # =========================
    if (
        website
        and website.code == "8book"
        and source_config
    ):
        secret = (
            source_config.get("secret")
        )

        booklist = (
            source_config.get("book_list")
        )

        if href.startswith("//"):
            href = "https:" + href

        parsed = urlparse(href)

        parts = (
            parsed.path
            .strip("/")
            .split("/")
        )

        if len(parts) < 2:
            return href

        book_id = parts[1]

        chapter_id = (
            parsed.query
        )

        return build_txt_url(
            base_url=website.base_url,
            book_id=book_id,
            chapter_id=chapter_id,
            secret=secret,
            book_list=booklist
        )

    # =========================
    # NORMAL URL HANDLING
    # =========================

    # absolute
    if href.startswith((
        "http://",
        "https://"
    )):
        return href

    parsed = urlparse(base_url)

    base_domain = (
        f"{parsed.scheme}"
        f"://{parsed.netloc}"
    )

    # protocol-relative
    if href.startswith("//"):

        return (
            f"{parsed.scheme}:{href}"
        )

    # root-relative
    if href.startswith("/"):

        return urljoin(
            base_domain,
            href
        )

    # =========================
    # UTF8 SLUG FIX
    # =========================

    current_slug = unquote(
        parsed.path
        .strip("/")
        .split("/")[0]
    )

    decoded_href = unquote(href)

    if decoded_href.startswith(
        current_slug + "/"
    ):

        return urljoin(
            base_domain + "/",
            href
        )

    # relative
    return urljoin(
        base_url,
        href
    )