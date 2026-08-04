import requests
from bs4 import BeautifulSoup

from core.news import NewsItem
from core.provider import Provider


class XProvider(Provider):

    SOURCES = (
        "FabrizioRomano",
        "MatteMoretto",
        "DiMarzio",
        "NicoSchira",
    )

    KEYWORDS = (
        "palermo",
        "palermo fc",
        "rosanero",
        "rosaneri",
        "inzaghi",
    )

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        )
    }

    @property
    def name(self) -> str:
        return "X Calciomercato"

    def fetch(self) -> list[NewsItem]:

        items: list[NewsItem] = []

        for source in self.SOURCES:

            print(
                f"Controllo X: @{source}"
            )

            # Placeholder:
            # il recupero dei post verrà collegato
            # al reader open source scelto

            continue

        return items
