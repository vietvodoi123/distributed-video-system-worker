from bs4 import BeautifulSoup


def extract_text_with_linebreaks(
    html: str
) -> str:

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for p in soup.find_all("p"):
        p.insert_after("\n")

    text = soup.get_text()

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    return "\n".join(lines).strip()