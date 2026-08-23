from pathlib import Path

# VERSIONE PALERMO SEARCH X - insider + keyword Palermo

import hashlib
import json
import re
from urllib.parse import quote_plus

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
    )

    @property
    def name(self):
        return "X Calciomercato"

    # ---------------------------------------------------------
    # KEYWORDS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # NORMALIZZAZIONE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # ID
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # CONTESTO PALERMO
    # ---------------------------------------------------------

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
        )

        normalized = text.casefold()

        return any(
            word in normalized
            for word in context_words
        )

    # ---------------------------------------------------------
    # PALERMO OFFICIAL
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # RILEVANZA
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # ESTRAZIONE IMMAGINE
    # ---------------------------------------------------------

    def extract_image(
        self,
        article: Locator
    ):

        try:

            # Metodo preferito: immagine allegata al tweet.
            tweet_photo = article.locator(
                '[data-testid="tweetPhoto"] img'
            )

            if tweet_photo.count() > 0:

                for i in range(
                    min(
                        tweet_photo.count(),
                        5
                    )
                ):

                    src = (
                        tweet_photo.nth(i)
                        .get_attribute("src")
                    )

                    if src and src.startswith(
                        "http"
                    ):

                        return src

            # Fallback: immagini dentro l'articolo.
            images = article.locator(
                "img"
            )

            for i in range(
                min(
                    images.count(),
                    10
                )
            ):

                image = images.nth(i)

                src = image.get_attribute(
                    "src"
                )

                if not src:
                    continue

                if not src.startswith(
                    "http"
                ):
                    continue

                alt = (
                    image.get_attribute(
                        "alt"
                    )
                    or ""
                ).casefold()

                # Evita avatar/profilo quando possibile.
                if (
                    "profile" in alt
                    or "avatar" in alt
                ):
                    continue

                return src

        except Exception as e:

            print(
                f"Errore estrazione immagine: {e}"
            )

        return ""

    # ---------------------------------------------------------
    # ESTRAZIONE TWEET
    # ---------------------------------------------------------

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

            # -------------------------------------------------
            # DATA / LINK
            # -------------------------------------------------

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

            # -------------------------------------------------
            # IMMAGINE
            # -------------------------------------------------

            image_url = self.extract_image(
                article
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

    # ---------------------------------------------------------
    # RACCOLTA TIMELINE
    # ---------------------------------------------------------

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
                f"Scroll {scroll + 1} - "
                f"articoli: {count}"
            )

            for i in range(count):

                post = self.extract_post(
                    articles.nth(i)
                )

                if not post:

                    continue

                (
                    text,
                    link,
                    published,
                    image_url
                ) = post

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

                if (
                    len(collected)
                    >= self.MAX_POSTS_PER_SOURCE
                ):

                    break

            if (
                len(collected)
                >= self.MAX_POSTS_PER_SOURCE
            ):

                break

            page.mouse.wheel(
                0,
                6000
            )

            page.wait_for_timeout(
                2500
            )

        print(
            f"Totale raccolti @{source}: "
            f"{len(collected)}"
        )

        return collected

    # ---------------------------------------------------------
    # RICERCA X MIRATA
    # ---------------------------------------------------------

    def search_x_posts(
        self,
        page: Page,
        source,
        query
    ):

        results = []

        try:

            # Codifica corretta della query X.
            url_query = quote_plus(
                query
            )

            url = (
                "https://x.com/search"
                f"?q={url_query}"
                "&f=live"
                "&src=typed_query"
            )

            print(
                f"CONTROLLO SEARCH X: {url}"
            )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                6000
            )

            articles = page.locator(
                "article"
            )

            count = articles.count()

            print(
                f"Search tweet trovati: {count}"
            )

            for i in range(
                min(count, 20)
            ):

                post = self.extract_post(
                    articles.nth(i)
                )

                if post:

                    results.append(
                        post
                    )

        except Exception as e:

            print(
                f"Errore ricerca X "
                f"{source} {query}: {e}"
            )

        return results

    # ---------------------------------------------------------
    # DEDUPLICAZIONE POST
    # ---------------------------------------------------------

    def merge_posts(
        self,
        posts
    ):

        merged = []

        seen = set()

        for post in posts:

            text = post[0]
            link = post[1]

            key = (
                link
                or self.normalize_text(
                    text
                )
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            merged.append(
                post
            )

        return merged

    # ---------------------------------------------------------
    # CONTROLLO INSIDER
    # ---------------------------------------------------------

    def is_allowed_insider(
        self,
        text
    ):

        return any(
            insider.casefold()
            in text.casefold()
            for insider
            in self.ALLOWED_INSIDERS
        )

    # ---------------------------------------------------------
    # QUERY MIRATE
    # ---------------------------------------------------------

    def get_search_queries(
        self,
        source
    ):

        queries = []

        # Prima scelta:
        # cerchiamo direttamente i post dell'account
        # che parlano del Palermo.
        queries.append(
            f"from:{source} Palermo"
        )

        # Seconda ricerca per intercettare
        # formulazioni con "rosanero".
        queries.append(
            f"from:{source} rosanero"
        )

        # Per account insider possiamo aggiungere
        # Palermo FC.
        if source != "Palermofficial":

            queries.append(
                f"from:{source} \"Palermo FC\""
            )

        return queries

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------

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

                    # -------------------------------------------------
                    # TIMELINE ACCOUNT
                    # -------------------------------------------------

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

                    # -------------------------------------------------
                    # RICERCHE MIRATE
                    # -------------------------------------------------

                    if source in self.ALLOWED_INSIDERS:

                        search_queries = (
                            self.get_search_queries(
                                source
                            )
                        )

                        for query in search_queries:

                            posts.extend(
                                self.search_x_posts(
                                    page,
                                    source,
                                    query
                                )
                            )

                    # -------------------------------------------------
                    # DEDUPLICAZIONE
                    # -------------------------------------------------

                    posts = self.merge_posts(
                        posts
                    )

                    print(
                        f"Post totali dopo dedup "
                        f"@{source}: {len(posts)}"
                    )

                    # -------------------------------------------------
                    # PROCESSAMENTO
                    # -------------------------------------------------

                    for post in posts:

                        (
                            text,
                            link,
                            published,
                            image_url
                        ) = post

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
                            f"ID GENERATO: "
                            f"{item_id}"
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
