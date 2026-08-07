from pathlib import Path
import hashlib
import json
import re

from playwright.sync_api import Locator, Page, sync_playwright

from core.news import NewsItem
from core.provider import Provider


class XProvider(Provider):

    SOURCES = (
        "FabrizioRomano",
        "MatteMoretto",
        "DiMarzio",
        "NicoSchira",
        "Palermofficial",
    )


    KEYWORDS_FILE = Path(
        "data/palermo_keywords.json"
    )


    MAX_POSTS_PER_SOURCE = 25


    @property
    def name(self):
        return "X Calciomercato"



    def load_keywords(self):

        with open(
            self.KEYWORDS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        return tuple(
            x.casefold()
            for x in data.get(
                "keywords",
                []
            )
        )



    def normalize_text(
        self,
        text
    ):

        text = text.casefold()


        text = re.sub(
            r"\b\d+\s*(m|h|d|w)\b",
            "",
            text
        )


        text = re.sub(
            r"\b\d+[km]?\b",
            "",
            text
        )


        text = re.sub(
            r"\s+",
            " ",
            text
        )


        return text.strip()



    def generate_id(
        self,
        source,
        text,
        link=""
    ):

        # Nuovo metodo:
        # usa ID tweet reale

        match = re.search(
            r"/status/(\d+)",
            link
        )


        if match:

            return (
                f"x-{source}-"
                f"{match.group(1)}"
            )


        # Compatibilità vecchi ID

        clean = self.normalize_text(
            text
        )


        digest = hashlib.sha256(
            f"{source}-{clean}".encode()
        ).hexdigest()


        return (
            f"x-{source}-"
            f"{digest[:16]}"
        )



    def is_market_post(
        self,
        text
    ):

        text = text.casefold()


        # esclusioni Palermo Official

        excluded = (

            "match day",

            "trophy",

            "torniamo in campo",

            "scendiamo in campo",

            "allenamento",

            "training",

            "partita",

            "gara",

            "diretta",

            "streaming",

            "live",

            "amichevole",

        )


        if any(
            word in text
            for word in excluded
        ):

            return False



        market = (

            "benvenuto",

            "welcome",

            "ufficiale",

            "annuncia",

            "annunciato",

            "firma",

            "firmato",

            "contratto",

            "rinnovo",

            "prolungamento",

            "acquisto",

            "acquista",

            "ingaggiato",

            "ceduto",

            "cessione",

            "prestito",

            "transfer",

            "signing",

            "signed",

        )


        return any(
            word in text
            for word in market
        )



    def is_relevant(
        self,
        text,
        source
    ):

        normalized = text.casefold()



        if source == "Palermofficial":

            result = self.is_market_post(
                normalized
            )


            if result:

                print(
                    "Post mercato Palermo ufficiale"
                )

            else:

                print(
                    "Palermo Official scartato"
                )


            return result



        keywords = self.load_keywords()



        for keyword in keywords:

            if keyword in normalized:

                print(
                    f"Keyword trovata: {keyword}"
                )

                return True



        return False



    def extract_post(
        self,
        article: Locator
    ):

        try:

            text_box = article.locator(
                '[data-testid="tweetText"]'
            )


            if text_box.count() == 0:

                return None


            text = text_box.inner_text()



            time = article.locator(
                "time"
            )


            link = ""

            published = ""


            if time.count():

                published = (
                    time.get_attribute(
                        "datetime"
                    )
                    or ""
                )


                parent = time.locator(
                    "xpath=.."
                )


                href = parent.get_attribute(
                    "href"
                )


                if href:

                    link = (
                        "https://x.com"
                        + href
                    )



            return (
                text,
                link,
                published
            )


        except Exception:

            return None



    def fetch(self):

        items = []


        with sync_playwright() as p:


            browser = p.chromium.launch(
                headless=True
            )


            page = browser.new_page()



            for source in self.SOURCES:


                print(
                    f"\nCONTROLLO X: @{source}"
                )


                try:

                    page.goto(
                        f"https://x.com/{source}",
                        wait_until="domcontentloaded",
                        timeout=60000
                    )


                    page.wait_for_timeout(
                        5000
                    )



                    articles = page.locator(
                        "article"
                    )


                    count = articles.count()


                    print(
                        f"Tweet trovati: {count}"
                    )



                    for i in range(
                        min(
                            count,
                            self.MAX_POSTS_PER_SOURCE
                        )
                    ):


                        post = self.extract_post(
                            articles.nth(i)
                        )


                        if not post:

                            continue



                        text, link, published = post



                        print(
                            "\n--- POST ---"
                        )

                        print(
                            text[:300]
                        )



                        if not self.is_relevant(
                            text,
                            source
                        ):

                            continue



                        item_id = self.generate_id(
                            source,
                            text,
                            link
                        )



                        print(
                            f"ID GENERATO: {item_id}"
                        )



                        items.append(

                            NewsItem(

                                id=item_id,

                                title=text[:120],

                                link=link,

                                source=self.name,

                                published=published,

                                summary=text

                            )

                        )


                except Exception as e:

                    print(
                        f"Errore @{source}: {e}"
                    )



            browser.close()



        return items
