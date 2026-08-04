from pathlib import Path
import json
from datetime import datetime

from playwright.sync_api import sync_playwright

from core.news import NewsItem
from core.provider import Provider


class XProvider(Provider):

    SOURCES = (
        "FabrizioRomano",
        "MatteMoretto",
        "DiMarzio",
        "NicoSchira",
    )

    KEYWORDS_FILE = Path(
        "data/palermo_keywords.json"
    )


    @property
    def name(self) -> str:
        return "X Calciomercato"


    def load_keywords(self):

        try:

            with open(
                self.KEYWORDS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            return tuple(
                data.get(
                    "keywords",
                    []
                )
            )

        except Exception:

            return ()


    def clean_text(
        self,
        text: str
    ) -> str:

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.lower() == "pinned":
                continue

            if line.startswith("@"):
                continue

            lines.append(line)


        return " ".join(lines)


    def is_relevant(
        self,
        text: str
    ) -> bool:

        keywords = self.load_keywords()

        normalized = text.casefold()

        return any(
            keyword.casefold()
            in normalized
            for keyword in keywords
        )


    def fetch(self) -> list[NewsItem]:

        items: list[NewsItem] = []

        keywords = self.load_keywords()

        if not keywords:
            return items


        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()


            for source in self.SOURCES:

                print(
                    f"Controllo X: @{source}"
                )

                try:

                    url = (
                        f"https://x.com/{source}"
                    )


                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )


                    page.wait_for_timeout(
                        5000
                    )


                    tweets = page.locator(
                        "article"
                    )


                    count = tweets.count()


                    for i in range(
                        min(count, 5)
                    ):


                        raw = tweets.nth(i).inner_text()


                        text = self.clean_text(
                            raw
                        )


                        if not text:
                            continue


                        if not self.is_relevant(
                            text
                        ):
                            continue


                        items.append(

                            NewsItem(

                                id=(
                                    f"x-{source}-"
                                    f"{hash(text)}"
                                ),

                                title=text[:120],

                                link=url,

                                source=self.name,

                                published=(
                                    datetime.now()
                                    .isoformat()
                                ),

                                summary=text,

                            )

                        )


                except Exception as e:

                    print(
                        f"Errore X @{source}: {e}"
                    )


            browser.close()


        return items
