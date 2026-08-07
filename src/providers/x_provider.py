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


    MAX_POSTS_PER_SOURCE = 50



    @property
    def name(self):

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

                keyword.casefold()

                for keyword in data.get(
                    "keywords",
                    []
                )

            )


        except Exception:

            return ()



    def normalize_text(
        self,
        text
    ):


        text = text.casefold()



        # elimina orari X:
        # 5m - 2h - 1d

        text = re.sub(

            r"\b\d+\s*(m|h|d|w)\b",

            "",

            text

        )



        # elimina numeri statistiche

        text = re.sub(

            r"\b\d+[km]?\b",

            "",

            text

        )



        # elimina spazi doppi

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



        # fallback

        clean = self.normalize_text(
            text
        )


        digest = hashlib.sha256(

            f"{source}-{clean}".encode(
                "utf-8"
            )

        ).hexdigest()



        return (

            f"x-{source}-"
            f"{digest[:16]}"

        )



    def is_market_palermo_context(
        self,
        text
    ):


        context_words = (

            "palermo",

            "palerm",

            "rosanero",

            "almena",

            "al-qadisiyya",

            "al-qadisiyah",

            "al qadisiyya",

            "osti",

            "inzaghi",

            "strefezza",

            "pohjanpalo",

            "mercato",

            "calciomercato",

            "transfer",

        )



        normalized = text.casefold()



        return any(

            word in normalized

            for word in context_words

        )



    def is_market_post_official(
        self,
        text
    ):


        normalized = text.casefold()



        excluded = (

            "match day",

            "trophy",

            "allenamento",

            "training",

            "partita",

            "gara",

            "diretta",

            "streaming",

            "live",

            "amichevole",

            "risveglio",

            "perth",

        )



        if any(

            word in normalized

            for word in excluded

        ):

            return False



        market_words = (

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

            word in normalized

            for word in market_words

        )



    def is_relevant(
        self,
        text,
        source
    ):


        if source == "Palermofficial":

            result = self.is_market_post_official(
                text
            )


            print(

                "Palermo Official mercato:",
                result

            )


            return result



        return self.is_market_palermo_context(
            text
        )
    def extract_post(
        self,
        article: Locator
    ):

        try:

            tweet_box = article.locator(
                '[data-testid="tweetText"]'
            )


            if tweet_box.count() == 0:

                return None



            text = tweet_box.inner_text()



            time_element = article.locator(
                "time"
            )


            link = ""

            published = ""



            if time_element.count() > 0:


                published = (
                    time_element.get_attribute(
                        "datetime"
                    )
                    or ""
                )



                parent = time_element.locator(
                    "xpath=.."
                )


                href = parent.get_attribute(
                    "href"
                )


                if href:

                    if href.startswith(
                        "http"
                    ):

                        link = href

                    else:

                        link = (
                            "https://x.com"
                            + href
                        )



            return (
                text,
                link,
                published
            )



        except Exception as e:

            print(
                f"Errore estrazione tweet: {e}"
            )

            return None



    def collect_posts(
        self,
        page: Page,
        source
    ):


        collected = []

        already_seen = set()



        for scroll in range(12):


            articles = page.locator(
                "article"
            )


            count = articles.count()



            print(
                f"Scroll {scroll + 1} - articoli: {count}"
            )



            for i in range(count):


                post = self.extract_post(
                    articles.nth(i)
                )



                if not post:

                    continue



                text, link, published = post



                unique = (
                    link
                    or self.normalize_text(
                        text
                    )
                )



                if unique in already_seen:

                    continue



                already_seen.add(
                    unique
                )



                collected.append(
                    (
                        text,
                        link,
                        published
                    )
                )



                if len(collected) >= self.MAX_POSTS_PER_SOURCE:

                    break



            if len(collected) >= self.MAX_POSTS_PER_SOURCE:

                break



            # scroll timeline

            page.mouse.wheel(
                0,
                6000
            )


            page.wait_for_timeout(
                2500
            )



        print(
            f"Totale raccolti @{source}: {len(collected)}"
        )



        return collected




    def fetch(self):


        items = []


        with sync_playwright() as p:



            browser = p.chromium.launch(
                headless=True
            )



            page = browser.new_page(
                viewport={
                    "width": 1280,
                    "height": 1800
                }
            )



            for source in self.SOURCES:



                print(
                    "\n===================="
                )


                print(
                    f"CONTROLLO X: @{source}"
                )



                try:


                    page.goto(

                        f"https://x.com/{source}",

                        wait_until="domcontentloaded",

                        timeout=60000

                    )



                    page.wait_for_timeout(
                        6000
                    )



                    posts = self.collect_posts(
                        page,
                        source
                    )



                    for (
                        text,
                        link,
                        published
                    ) in posts:



                        print(
                            "\n--- POST ---"
                        )


                        print(
                            text[:400]
                        )



                        if not self.is_relevant(
                            text,
                            source
                        ):

                            print(
                                "Scartato"
                            )

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
