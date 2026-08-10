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
        Palermo Official: accetta contenuti sportivi e di mercato
        relativi alla prima squadra. Esclude contenuti commerciali,
        community e academy.
        """
        normalized = text.casefold()

        excluded = (
            "biglietto",
            "biglietti",
            "ticket",
            "store",
            "shop",
            "community",
            "sponsor",
            "marketing",
            "academy",
            "junior",
            "codice etico",
        )

        if any(word in normalized for word in excluded):
            return False

        return True

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

            text = ""


            # Metodo principale

            tweet_box = article.locator(
                '[data-testid="tweetText"]'
            )


            if tweet_box.count() > 0:

                text = tweet_box.inner_text()



            else:

                # Fallback nuovo layout X

                text = article.inner_text()



            if not text.strip():

                return None



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



            image_url = ""

            # Foto originale del tweet (se presente).
            # Evita avatar/profile images: X usa tweetPhoto per i media del post.
            photo = article.locator('[data-testid="tweetPhoto"] img')
            if photo.count() > 0:
                image_url = photo.first.get_attribute("src") or ""

            # Debug mirato + fallback: X può cambiare il wrapper delle immagini.
            # Per i tweet Palermo controlliamo anche tutte le immagini pbs.twimg.com/media.
            if "@Palermofficial" in text or "Palermo F.C." in text or "Palermo FC" in text:
                all_imgs = article.locator("img")
                print(f"MEDIA DEBUG @Palermofficial - img trovate: {all_imgs.count()}")
                for i in range(all_imgs.count()):
                    src = all_imgs.nth(i).get_attribute("src") or ""
                    if "pbs.twimg.com/media/" in src:
                        print(f"MEDIA DEBUG candidate: {src}")
                        if not image_url:
                            image_url = src

                print(
                    "MEDIA DEBUG scelta:",
                    image_url if image_url else "NESSUNA FOTO"
                )

            return (
                text,
                link,
                published,
                image_url
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



        for scroll in range(50):


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



                text, link, published, image_url = post



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
                        published,
                        image_url
                    )
                )



                if len(collected) >= self.MAX_POSTS_PER_SOURCE:

                    break



            if len(collected) >= self.MAX_POSTS_PER_SOURCE:

                break



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






    def search_x_posts(self, page: Page, source, query):
        results = []

        try:
            url_query = f"{query}"
            url = f"https://x.com/search?q={url_query}&f=live&src=typed_query"

            print(f"CONTROLLO SEARCH X: {url}")

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(6000)

            print("===== SEARCH X DISABLED =====")
            print("URL:", page.url)
            print("TITLE:", page.title())

            try:
                body_preview = page.locator("body").inner_text(timeout=10000)
                print("BODY PREVIEW:")
                print(body_preview[:1000])
            except Exception as e:
                print("Errore lettura body:", e)

            print("==========================")

            articles = page.locator("article")
            count = articles.count()

            print(f"Search tweet trovati: {count}")

            for i in range(min(count, 10)):
                post = self.extract_post(articles.nth(i))

                if post:
                    results.append(post)

        except Exception as e:
            print(f"Errore ricerca X {source} {query}: {e}")

        return results


    def merge_posts(self, posts):
        merged = []
        seen = set()

        for post in posts:
            text, link, published, image_url = post
            key = link or self.normalize_text(text)

            if key in seen:
                continue

            seen.add(key)
            merged.append(post)

        return merged



    def is_allowed_insider(self, text):
        return any(
            insider.casefold() in text.casefold()
            for insider in self.ALLOWED_INSIDERS
        )


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
                        published,
                        image_url
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

                                summary=text,

                                image_url=image_url

                            )

                        )



                except Exception as e:

                    print(
                        f"Errore @{source}: {e}"
                    )



            browser.close()



        return items
