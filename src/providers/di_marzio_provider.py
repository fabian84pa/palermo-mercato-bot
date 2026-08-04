from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.gianlucadimarzio.com/"
NEWS_URL = "https://www.gianlucadimarzio.com/news-calcio/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36"
    )
}

PALERMO_KEYWORDS = (
    "palermo",
    "palermo fc",
    "rosanero",
    "rosaneri",
)


@dataclass
class DiMarzioNews:
    item_id: str
    title: str
    link: str
    source: str


def is_palermo_news(title: str) -> bool:
    text = title.casefold()
    return any(keyword in text for keyword in PALERMO_KEYWORDS)


def fetch_di_marzio_news(limit: int = 20) -> list[DiMarzioNews]:
    response = requests.get(
        NEWS_URL,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    news: list[DiMarzioNews] = []
    seen_links: set[str] = set()

    for anchor in soup.select("a[href]"):
        title = anchor.get_text(" ", strip=True)
        link = urljoin(BASE_URL, anchor.get("href", ""))

        if not title or len(title) < 20:
            continue

        if "gianlucadimarzio.com" not in link:
            continue

        if link in seen_links:
            continue

        if not is_palermo_news(title):
            continue

        seen_links.add(link)

        news.append(
            DiMarzioNews(
                item_id=link,
                title=title,
                link=link,
                source="Gianluca Di Marzio",
            )
        )

        if len(news) >= limit:
            break

    return news
