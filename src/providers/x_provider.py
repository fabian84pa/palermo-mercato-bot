from pathlib import Path
import hashlib
import json
import os
import re
from urllib.parse import quote

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

    # Profilo Chromium persistente dedicato al bot.
    # NON usare il profilo personale di Chrome.
    X_PROFILE_DIR = Path(
        os.getenv(
            "X_PROFILE_DIR",
            "data/x_browser_profile"
        )
    )

    # Prima esecuzione:
    # X_HEADLESS=false
    #
    # Dopo aver effettuato il login:
    # X_HEADLESS=true
    X_HEADLESS = (
        os.getenv(
            "X_HEADLESS",
            "true"
        ).lower()
        not in (
            "0",
            "false",
            "no",
        )
    )

    MAX_POSTS_PER_SOURCE = 50

    SEARCH_QUERIES = {
        "MatteMoretto": [
            "Palermo",
            "rosanero",
            "Almena",
            "Osti",
            "Inzaghi",
            "Strefezza",
            "Pohjanpalo",
        ],

        "FabrizioRomano": [
            "Palermo",
            "rosanero",
            "Palermo FC",
        ],

        "DiMarzio": [
            "Palermo",
            "rosanero",
            "Palermo FC",
        ],

        "NicoSchira": [
            "Palermo",
            "rosanero",
            "Palermo FC",
        ],
    }

    # Termini utilizzati per identificare il contesto Palermo.
    PALERMO_CONTEXT = (
        "palermo",
        "palermo fc",
        "palermofficial",
        "rosanero",
        "rosaneri",
        "almena",
        "al-qadisiyya",
        "al-qadisiyah",
        "al qadisiyya",
        "osti",
        "inzaghi",
        "strefezza",
        "pohjanpalo",
    )

    @property
    def name(self):
        return "X Calciomercato"

    # ==========================================================
    # KEYWORDS
    # ==========================================================

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

    # ==========================================================
    # NORMALIZZAZIONE
    # ==========================================================

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

    # ==========================================================
    # ID
    # ==========================================================

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

    # ==========================================================
    # CONTESTO PALERMO
    # ==========================================================

    def is_market_palermo_context(
        self,
        text
    ):

        normalized = (
            text or ""
        ).casefold()

        return any(
            word in normalized
            for word in self.PALERMO_CONTEXT
        )

    # ==========================================================
    # FILTRO PALERMO OFFICIAL
    # ==========================================================

    def is_market_post_official(
        self,
        text
    ):

        normalized = (
            text or ""
        ).casefold()

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

    # ==========================================================
    # RILEVANZA
    # ==========================================================

    def is_relevant(
        self,
        text,
        source
    ):

        if source == "Palermofficial":

            result = (
                self.is_market_post_official(
                    text
                )
            )

            print(
                "Palermo Official mercato:",
                result
            )

            return result

        return self.is_market_palermo_context(
            text
        )

    # ==========================================================
    # ESTRAZIONE POST
    # ==========================================================

    def extract_post(
        self,
        article: Locator
    ):

        try:

            text = ""

            tweet_box = article.locator(
                '[data-testid="tweetText"]'
            )

            if tweet_box.count() > 0:

                text = tweet_box.first.inner_text()

            else:

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
                    time_element.first.get_attribute(
                        "datetime"
                    )
                    or ""
                )

                # X normalmente mette il link
                # del post vicino al tag <time>.
                parent = (
                    time_element.first.locator(
                        "xpath=.."
                    )
                )

                href = parent.get_attribute(
                    "href"
                )

                if not href:

                    # Fallback: cerca un link
                    # /status/ dentro l'article.
                    status_links = article.locator(
                        'a[href*="/status/"]'
                    )

                    if status_links.count() > 0:

                        href = (
                            status_links.first.get_attribute(
                                "href"
                            )
                        )

                if href:

                    if href.startswith(
                        "http"
                    ):

                        link = href

                    elif href.startswith("/"):

                        link = (
                            "https://x.com"
                            + href
                        )

            return (
                text.strip(),
                link,
                published
            )

        except Exception as e:

            print(
                f"Errore estrazione tweet: {e}"
            )

            return None

    # ==========================================================
    # DIAGNOSTICA PAGINA X
    # ==========================================================

    def diagnose_page(
        self,
        page: Page,
        context=""
    ):

        try:

            current_url = page.url

            title = page.title()

            body_text = page.locator(
                "body"
            ).inner_text(
                timeout=5000
            )

            body_lower = (
                body_text or ""
            ).casefold()

            print(
                "\n--- DIAGNOSTICA X ---"
            )

            print(
                f"Contesto: {context}"
            )

            print(
                f"URL: {current_url}"
            )

            print(
                f"Titolo: {title}"
            )

            if (
                "accedi" in body_lower
                or "sign in" in body_lower
                or "log in" in body_lower
            ):

                print(
                    "ATTENZIONE: X sembra richiedere "
                    "l'accesso."
                )

            if (
                "non esiste" in body_lower
                or "doesn't exist" in body_lower
                or "page doesn't exist" in body_lower
            ):

                print(
                    "ATTENZIONE: X segnala "
                    "pagina inesistente."
                )

            if (
                "something went wrong"
                in body_lower
                or "qualcosa è andato storto"
                in body_lower
            ):

                print(
                    "ATTENZIONE: X segnala "
                    "un errore di caricamento."
                )

            if (
                "post" in body_lower
                or "posts" in body_lower
            ):

                print(
                    "La pagina contiene testo "
                    "relativo ai post."
                )

            print(
                "--- FINE DIAGNOSTICA ---"
            )

        except Exception as e:

            print(
                f"Errore diagnostica X: {e}"
            )

    # ==========================================================
    # RACCOLTA PROFILO
    # ==========================================================

    def collect_posts(
        self,
        page: Page,
        source
    ):

        collected = []

        already_seen = set()

        empty_rounds = 0

        for scroll in range(12):

            articles = page.locator(
                "article"
            )

            count = articles.count()

            print(
                f"Scroll {scroll + 1} "
                f"- articoli: {count}"
            )

            if count == 0:

                empty_rounds += 1

            else:

                empty_rounds = 0

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

            # Se per tre cicli consecutivi
            # X non mostra nemmeno un article,
            # non ha senso continuare a scrollare.
            if empty_rounds >= 3:

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

        if not collected:

            self.diagnose_page(
                page,
                f"profilo @{source}"
            )

        return collected

    # ==========================================================
    # RICERCA X
    # ==========================================================

    def search_x_posts(
        self,
        page: Page,
        source,
        query
    ):

        results = []

        try:

            full_query = (
                f"from:{source} {query}"
            )

            encoded_query = quote(
                full_query,
                safe=""
            )

            url = (
                "https://x.com/search"
                f"?q={encoded_query}"
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
                8000
            )

            # Attende eventualmente il caricamento
            # dinamico degli article.
            try:

                page.locator(
                    "article"
                ).first.wait_for(
                    state="visible",
                    timeout=12000
                )

            except Exception:

                pass

            articles = page.locator(
                "article"
            )

            count = articles.count()

            print(
                f"Search tweet trovati: {count}"
            )

            if count == 0:

                self.diagnose_page(
                    page,
                    f"search @{source} - {query}"
                )

            for i in range(
                min(
                    count,
                    20
                )
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

    # ==========================================================
    # DEDUPLICAZIONE
    # ==========================================================

    def merge_posts(
        self,
        posts
    ):

        merged = []

        seen = set()

        for post in posts:

            text, link, published = post

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

    # ==========================================================
    # CONTROLLO SESSIONE X
    # ==========================================================

    def check_x_session(
        self,
        page
    ):

        try:

            page.goto(
                "https://x.com/home",
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                5000
            )

            url = page.url

            body = page.locator(
                "body"
            ).inner_text(
                timeout=5000
            )

            body_lower = (
                body or ""
            ).casefold()

            print(
                "\n===================="
            )

            print(
                "CONTROLLO SESSIONE X"
            )

            print(
                f"URL sessione: {url}"
            )

            if (
                "/login" in url
                or "/i/flow/login" in url
                or "accedi" in body_lower
                or "sign in" in body_lower
                or "log in" in body_lower
            ):

                print(
                    "SESSIONE X NON AUTENTICATA."
                )

                print(
                    "Per la prima configurazione "
                    "esegui il bot con X_HEADLESS=false "
                    "e accedi a X nel browser che si apre."
                )

                print(
                    "Dopo il login, chiudi il browser "
                    "e riesegui il bot con X_HEADLESS=true."
                )

                return False

            print(
                "Sessione X disponibile."
            )

            return True

        except Exception as e:

            print(
                f"Errore controllo sessione X: {e}"
            )

            return False

    # ==========================================================
    # FETCH
    # ==========================================================

    def fetch(self):

        items = []

        self.X_PROFILE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        print(
            "\n===================="
        )

        print(
            "X PROVIDER"
        )

        print(
            f"Profilo X: {self.X_PROFILE_DIR}"
        )

        print(
            f"Headless: {self.X_HEADLESS}"
        )

        with sync_playwright() as p:

            context = None

            try:

                context = (
                    p.chromium
                    .launch_persistent_context(
                        user_data_dir=str(
                            self.X_PROFILE_DIR
                        ),
                        headless=self.X_HEADLESS,
                        viewport={
                            "width": 1280,
                            "height": 1800
                        },
                        locale="it-IT",
                        timezone_id="Europe/Rome",
                        args=[
                            "--disable-blink-features=AutomationControlled",
                        ],
                    )
                )

                # Usa una pagina già presente,
                # oppure ne crea una nuova.
                if context.pages:

                    page = context.pages[0]

                else:

                    page = context.new_page()

                # --------------------------------------------------
                # CONTROLLO SESSIONE
                # --------------------------------------------------

                session_ok = (
                    self.check_x_session(
                        page
                    )
                )

                if not session_ok:

                    # Se siamo in modalità non-headless,
                    # lasciamo tempo all'utente di effettuare
                    # il login manualmente.
                    if not self.X_HEADLESS:

                        print(
                            "\nATTENDO IL LOGIN X..."
                        )

                        print(
                            "Accedi a X nella finestra "
                            "del browser."
                        )

                        print(
                            "Hai 120 secondi."
                        )

                        try:

                            page.wait_for_timeout(
                                120000
                            )

                        except Exception:

                            pass

                        session_ok = (
                            self.check_x_session(
                                page
                            )
                        )

                    if not session_ok:

                        print(
                            "\nRaccolta X interrotta: "
                            "sessione non disponibile."
                        )

                        return items

                # --------------------------------------------------
                # RACCOLTA ACCOUNT
                # --------------------------------------------------

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
                            8000
                        )

                        # Attesa dinamica.
                        try:

                            page.locator(
                                "article"
                            ).first.wait_for(
                                state="visible",
                                timeout=12000
                            )

                        except Exception:

                            pass

                        posts = (
                            self.collect_posts(
                                page,
                                source
                            )
                        )

                        # --------------------------------------------------
                        # RICERCHE SPECIFICHE
                        # --------------------------------------------------

                        if (
                            source
                            in self.SEARCH_QUERIES
                        ):

                            for query in (
                                self.SEARCH_QUERIES[
                                    source
                                ]
                            ):

                                posts.extend(
                                    self.search_x_posts(
                                        page,
                                        source,
                                        query
                                    )
                                )

                        posts = (
                            self.merge_posts(
                                posts
                            )
                        )

                        print(
                            f"Post totali dopo dedup "
                            f"@{source}: "
                            f"{len(posts)}"
                        )

                        # --------------------------------------------------
                        # FILTRO E CREAZIONE NEWS
                        # --------------------------------------------------

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

                            item_id = (
                                self.generate_id(
                                    source,
                                    text,
                                    link
                                )
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
                                    summary=text
                                )
                            )

                    except Exception as e:

                        print(
                            f"Errore @{source}: {e}"
                        )

            finally:

                if context:

                    try:

                        context.close()

                    except Exception:

                        pass

        print(
            "\n===================="
        )

        print(
            f"X PROVIDER: "
            f"{len(items)} notizie valide"
        )

        print(
            "===================="
        )

        return items
