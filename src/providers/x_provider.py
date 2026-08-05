from pathlib import Path
import json
import hashlib
import re
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

        with open(
            self.KEYWORDS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        return tuple(
            data.get("keywords", [])
        )



    def clean_text(self, text):

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



    def is_relevant(self, text):

        keywords = self.load_keywords()

        normalized = text.casefold()


        for keyword in keywords:

            if keyword.casefold() in normalized:

                print(
                    f"Keyword trovata: {keyword}"
                )

                return True


        return False



    def generate_id(
        self,
        source,
        text
    ):

        """
        ID stabile per X.
        Ignora numeri, visualizzazioni,
        like e statistiche variabili.
        """

        clean = text.casefold()


        # elimina numeri tipo:
        # 50K - 120 - 1.2M - orari
        clean = re.sub(
            r"\b\d+[kKmM]?\b",
            "",
            clean
        )


        # elimina caratteri inutili
        clean = re.sub(
            r"[^\w\s@#]",
            " ",
            clean
        )


        # normalizza spazi
        clean = " ".join(
            clean.split()
        )


        unique_text = (
            f"{source}-{clean}"
        )


        hash_value = hashlib.sha256(
            unique_text.encode("utf-8")
        ).hexdigest()


        return (
            f"x-{source}-{hash_value[:16]}"
        )



    def fetch(self) -> list[NewsItem]:

        items = []


        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )


            page = browser.new_page()



            for source in self.SOURCES:


                print(
                    "\n===================="
                )


                print(
                    f"CONTROLLO X: @{source}"
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
                        8000
                    )



                    tweets = page.locator(
                        "article"
                    )


                    count = tweets.count()


                    print(
                        f"Tweet trovati: {count}"
                    )



                    for i in range(
                        min(count, 5)
                    ):


                        raw = tweets.nth(i).inner_text()



                        print(
                            "\n--- RAW TWEET ---"
                        )


                        print(
                            raw[:300]
                        )



                        text = self.clean_text(
                            raw
                        )



                        print(
                            "\n--- PULITO ---"
                        )


                        print(
                            text[:300]
                        )



                        if not self.is_relevant(
                            text
                        ):

                            print(
                                "Scartato"
                            )

                            continue



                        item_id = self.generate_id(
                            source,
                            text
                        )


                        print(
                            f"ID GENERATO: {item_id}"
                        )



                        items.append(

                            NewsItem(

                                id=item_id,


                                title=text[:120],


                                link=url,


                                source=self.name,


                                published=datetime.now().isoformat(),


                                summary=text

                            )

                        )



                except Exception as e:

                    print(
                        f"Errore @{source}: {e}"
                    )



            browser.close()



        return items
