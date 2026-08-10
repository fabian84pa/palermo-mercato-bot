# VERSIONE PALERMO v9 - raccolta profili estesa\nfrom pathlib import Path
# VERSIONE PALERMO SEARCH X - insider + keyword Palermo
from pathlib import Path
import hashlib
import json
import re

from playwright.sync_api import Locator, Page, sync_playwright

from core.news import NewsItem
from core.provider import Provider



class XProvider(Provider):

    INSIDER_NAMES_TO_IGNORE = (
        "Matteo Moretto",
        "Fabrizio Romano",
        "Nico Schira",
        "Gianluca Di Marzio",
    )




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

    ALLOWED_INSIDERS = (
        "MatteMoretto",
        "DiMarzio",
        "FabrizioRomano",
        "NicoSchira",
        "Palermofficial",
    )



    SEARCH_TERMS = (
        "Palermo",
        "Palermo FC",
        "rosanero",
        "rosaneri",
        "aquile",
        "Almena",
        "Osti",
        "Inzaghi",
        "Strefezza",
        "Pohjanpalo",
    )



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


        match = re.search(
            r"/status/(\d+)",
            link
        )


        if match:

            return (
                f"x-{source}-"
                f"{match.group(1)}"
            )



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



    def is_market_palermo_context(self, text):
        """Accetta solo tweet con riferimento esplicito al Palermo."""
        normalized = text.casefold()
        palermo_markers = (
            "palermo",
            "palermo fc",
            "@palermofficial",
            "rosanero",
            "rosaneri",
        )
        return any(marker in normalized for marker in palermo_markers)


    def is_market_post_official(self, text):
        """
        Palermo Official: accetta contenuti sportivi/mercato sulla prima squadra.
        Esclude contenuti commerciali, community e academy.
        """
        normalized = text.casefold()

        excluded = (
            "biglietto", "biglietti", "ticket", "store", "shop",
            "community", "sponsor", "marketing", "academy", "junior",
            "codice etico", "birthday", "buon compleanno",
        )

        if any(word in normalized for word in excluded):
            return False

        return True


    def clean_x_timestamp(self, text):
        patterns = [
            r"(?mi)^\s*\d+\s*[mhdw]\s*$",
            r"(?mi)^\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*$",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text)
        return text.strip()

    def clean_x_display_text(self, text):
        """Rimuove timestamp e contatori X isolati, non i numeri nelle frasi."""
        if not text:
            return ""

        cleaned = []
        counter_re = re.compile(r"^\s*\d+(?:[.,]\d+)?[KMB]?\s*$", re.I)
        time_re = re.compile(
            r"^\s*(?:\d+\s*[mhdw]|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s*$",
            re.I,
        )

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if time_re.fullmatch(stripped) or counter_re.fullmatch(stripped):
                continue
            cleaned.append(line)

        return "\n".join(cleaned).strip()

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

                    # Ricerca X globale per parole chiave Palermo
                    if source in self.ALLOWED_INSIDERS:

                        for query in []:

                            posts.extend(
                                self.search_x_posts(
                                    page,
                                    source,
                                    query
                                )
                            )

                    posts = self.merge_posts(posts)



                    for (
                        text,
                        link,
                        published
                    ) in posts:


                        
                        text = self.clean_x_display_text(text)

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
