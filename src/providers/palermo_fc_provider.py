from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from core.news import NewsItem
from core.provider import Provider


class PalermoFCProvider(Provider):

    BASE_URL = "https://www.palermofc.com"
    NEWS_URL = "https://www.palermofc.com/news"

    KEYWORDS = (
        "ufficiale",
        "firma",
        "firmato",
        "nuovo acquisto",
        "acquista",
        "ingaggia",
        "benvenuto",
        "arriva",
        "cessione",
        "rinnovo",
        "prolungamento",
    )

    EXCLUDED_KEYWORDS = (
        "community",
        "codice etico",
        "biglietteria",
        "store",
        "ticket",
        "sponsor",
        "marketing",
        "junior",
        "academy",
    )

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/150.0.0.0 Safari/537.36"
        )
    }

    @property
    def name(self) -> str:
        return "Palermo FC"

    def get_summary(self, link: str) -> str:
        try:
            response = requests.get(
                link,
                headers=self.HEADERS,
                timeout=15,
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            description = soup.find(
                "meta",
                attrs={"name": "description"}
            )

            if description and description.get("content"):
                return description["content"].strip()

        except Exception:
            pass

        return ""

    def is_market_news(self, title: str) -> bool:

        text = title.casefold()

        if any(
            keyword in text
            for keyword in self.EXCLUDED_KEYWORDS
        ):
            return False

        return any(
            keyword in text
            for keyword in self.KEYWORDS
        )

    def fetch(self) -> list[NewsItem]:

        response = requests.get(
            self.NEWS_URL,
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        items: list[NewsItem] = []
        seen_links: set[str] = set()

        for anchor in soup.find_all("a", href=True):

            title = anchor.get_text(
                " ",
                strip=True
            )

            href = anchor["href"].strip()

            if not title or len(title) < 15:
                continue

            if not self.is_market_news(title):
                continue

            link = urljoin(
                self.BASE_URL,
                href
            )

            if link in seen_links:
                continue

            seen_links.add(link)

            items.append(
                NewsItem(
                    id=link,
                    title=title,
                    link=link,
                    source=self.name,
                    published="",
                    summary=self.get_summary(link),
                )
            )

        return items
