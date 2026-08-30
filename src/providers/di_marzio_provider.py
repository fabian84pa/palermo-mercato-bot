from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from core.news import NewsItem
from core.provider import Provider


class DiMarzioProvider(Provider):

    BASE_URL = "https://www.gianlucadimarzio.com"

    NEWS_URLS = (
        "https://www.gianlucadimarzio.com/calciomercato/",
        "https://www.gianlucadimarzio.com/",
    )

    # ==========================================================
    # KEYWORDS PALERMO
    # ==========================================================
    #
    # Sono divise per importanza.
    #
    # Palermo / rosanero = identificazione diretta.
    # Giocatori / dirigenti = identificazione di un'operazione
    # che può essere scritta senza nominare Palermo nel titolo.
    #

    PALERMO_KEYWORDS = (
        "palermo",
        "palermo fc",
        "palermo calcio",
        "rosanero",
        "rosaneri",
    )

    PEOPLE_KEYWORDS = (
        "inzaghi",
        "pohjanpalo",
        "gabrielloni",
        "almena",
        "osti",
        "strefezza",
        "perin",
        "sportiello",
        "semper",
        "brunori",
        "audero",
        "thiam",
        "kostic",
    )

    # ==========================================================
    # PAROLE DA IGNORARE
    # ==========================================================
    #
    # Queste parole da sole NON possono dimostrare che
    # un articolo riguarda il Palermo.
    #

    GENERIC_WORDS = (
        "arrivo",
        "arriva",
        "arrivato",
        "arrivata",
        "giocatore",
        "giocatori",
        "calciomercato",
        "mercato",
        "accordo",
        "offerta",
        "trattativa",
        "interesse",
        "profilo",
        "profili",
        "nuovo",
        "nuova",
        "firma",
        "firmato",
        "firmata",
        "prestito",
        "cessione",
        "acquisto",
        "ufficiale",
        "visite mediche",
    )

    # ==========================================================
    # HTTP
    # ==========================================================

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept-Language": (
            "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,"
            "image/apng,*/*;q=0.8"
        ),
    }

    TIMEOUT = 30

    # ==========================================================
    # PROVIDER NAME
    # ==========================================================

    @property
    def name(self) -> str:
        return "Gianluca Di Marzio"

    # ==========================================================
    # GET PAGE
    # ==========================================================

    def get_page(
        self,
        url: str,
    ):
        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=self.TIMEOUT,
        )

        response.raise_for_status()

        return BeautifulSoup(
            response.text,
            "html.parser",
        )

    # ==========================================================
    # META
    # ==========================================================

    @staticmethod
    def get_meta(
        soup: BeautifulSoup,
        *,
        name: str = None,
        prop: str = None,
    ) -> str:

        attrs = {}

        if name:
            attrs["name"] = name

        if prop:
            attrs["property"] = prop

        tag = soup.find(
            "meta",
            attrs=attrs,
        )

        if not tag:
            return ""

        return (
            tag.get("content")
            or ""
        ).strip()

    # ==========================================================
    # ARTICLE BODY
    # ==========================================================

    @staticmethod
    def get_article_text(
        soup: BeautifulSoup,
    ) -> str:
        """
        Estrae il testo dell'articolo.

        Serve come terzo livello di controllo quando il titolo
        non contiene direttamente Palermo o un nome noto.

        Non usiamo tutto l'HTML indiscriminatamente perché menu,
        footer, articoli correlati e pubblicità possono contenere
        parole che falserebbero il filtro.
        """

        selectors = (
            "article",
            "[itemprop='articleBody']",
            ".article-body",
            ".article-content",
            ".post-content",
            ".entry-content",
            "main",
        )

        for selector in selectors:

            nodes = soup.select(
                selector
            )

            if not nodes:
                continue

            chunks = []

            for node in nodes:

                text = node.get_text(
                    " ",
                    strip=True,
                )

                if text:
                    chunks.append(
                        text
                    )

            if chunks:

                return " ".join(
                    chunks
                )

        # Fallback molto conservativo.
        body = soup.find(
            "body"
        )

        if body:

            return body.get_text(
                " ",
                strip=True,
            )

        return ""

    # ==========================================================
    # ARTICLE DATA
    # ==========================================================

    def get_article_data(
        self,
        link: str,
    ):

        try:

            soup = self.get_page(
                link
            )

            summary = (
                self.get_meta(
                    soup,
                    name="description",
                )
                or self.get_meta(
                    soup,
                    prop="og:description",
                )
            )

            image_url = self.get_meta(
                soup,
                prop="og:image",
            )

            published = (
                self.get_meta(
                    soup,
                    prop="article:published_time",
                )
                or self.get_meta(
                    soup,
                    name="date",
                )
            )

            if not published:

                time_tag = soup.find(
                    "time"
                )

                if time_tag:

                    published = (
                        time_tag.get(
                            "datetime"
                        )
                        or time_tag.get_text(
                            " ",
                            strip=True,
                        )
                    )

            article_text = (
                self.get_article_text(
                    soup
                )
            )

            return (
                summary,
                image_url,
                published,
                article_text,
            )

        except Exception as e:

            print(
                f"Di Marzio: errore articolo "
                f"{link}: {e}"
            )

            return (
                "",
                "",
                "",
                "",
            )

    # ==========================================================
    # CLEAN TITLE
    # ==========================================================

    @staticmethod
    def clean_title(
        title: str,
    ) -> str:

        title = (
            title
            or ""
        )

        title = " ".join(
            title.split()
        )

        return title.strip()

    # ==========================================================
    # VALID ARTICLE LINK
    # ==========================================================

    def is_article_link(
        self,
        link: str,
    ) -> bool:

        if not link.startswith(
            self.BASE_URL
        ):
            return False

        clean_link = (
            link.rstrip("/")
        )

        if clean_link in (
            self.BASE_URL,
            f"{self.BASE_URL}/calciomercato",
        ):
            return False

        path = link.replace(
            self.BASE_URL,
            "",
        )

        if path in (
            "",
            "/",
            "/calciomercato/",
        ):
            return False

        excluded_parts = (
            "/tag/",
            "/categoria/",
            "/author/",
            "/search",
            "/login",
            "/page/",
            "/video/",
        )

        if any(
            part in path
            for part in excluded_parts
        ):
            return False

        return True

    # ==========================================================
    # NORMALIZE TEXT
    # ==========================================================

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:

        return " ".join(
            (text or "")
            .casefold()
            .split()
        )

    # ==========================================================
    # DIRECT PALERMO CHECK
    # ==========================================================

    def contains_palermo(
        self,
        text: str,
    ) -> bool:

        normalized = self.normalize_text(
            text
        )

        return any(
            keyword in normalized
            for keyword in self.PALERMO_KEYWORDS
        )

    # ==========================================================
    # KNOWN PLAYER CHECK
    # ==========================================================

    def contains_known_person(
        self,
        text: str,
    ) -> bool:

        normalized = self.normalize_text(
            text
        )

        return any(
            keyword in normalized
            for keyword in self.PEOPLE_KEYWORDS
        )

    # ==========================================================
    # PALERMO NEWS CHECK
    # ==========================================================

    def is_palermo_news(
        self,
        title: str,
        summary: str = "",
        article_text: str = "",
    ) -> bool:
        """
        Filtro a più livelli.

        LIVELLO 1:
        Palermo / Rosanero direttamente nel titolo.

        LIVELLO 2:
        Giocatore/dirigente noto direttamente nel titolo.

        LIVELLO 3:
        Se il titolo non basta, controlliamo summary + corpo
        dell'articolo cercando un riferimento forte al Palermo.

        NON consideriamo sufficienti parole generiche come:
        "arrivo", "accordo", "trattativa", "giocatore", ecc.
        """

        normalized_title = self.normalize_text(
            title
        )

        normalized_summary = self.normalize_text(
            summary
        )

        normalized_body = self.normalize_text(
            article_text
        )

        # ------------------------------------------------------
        # 1. PALERMO NEL TITOLO
        # ------------------------------------------------------

        if self.contains_palermo(
            normalized_title
        ):
            return True

        # ------------------------------------------------------
        # 2. GIOCATORE/OBIETTIVO NOTO NEL TITOLO
        # ------------------------------------------------------

        if self.contains_known_person(
            normalized_title
        ):
            return True

        # ------------------------------------------------------
        # 3. PALERMO NEL SUMMARY
        # ------------------------------------------------------

        if self.contains_palermo(
            normalized_summary
        ):
            return True

        # ------------------------------------------------------
        # 4. GIOCATORE NOTO + PALERMO NEL CORPO
        # ------------------------------------------------------

        if (
            self.contains_known_person(
                normalized_title
            )
            and self.contains_palermo(
                normalized_body
            )
        ):
            return True

        # ------------------------------------------------------
        # 5. PALERMO NEL CORPO
        # ------------------------------------------------------
        #
        # Richiediamo più di una semplice parola generica.
        # Se il corpo dell'articolo parla esplicitamente del
        # Palermo, è sufficiente.
        #

        if self.contains_palermo(
            normalized_body
        ):
            return True

        return False

    # ==========================================================
    # FETCH
    # ==========================================================

    def fetch(
        self,
    ) -> list[NewsItem]:

        items = []

        seen_links = set()

        print(
            "\n===================="
        )

        print(
            "CONTROLLO PROVIDER: "
            "Gianluca Di Marzio"
        )

        print(
            "===================="
        )

        for news_url in self.NEWS_URLS:

            print(
                f"Pagina Di Marzio: "
                f"{news_url}"
            )

            try:

                soup = self.get_page(
                    news_url
                )

            except Exception as e:

                print(
                    f"Di Marzio: errore "
                    f"pagina {news_url}: {e}"
                )

                continue

            anchors = soup.find_all(
                "a",
                href=True,
            )

            print(
                f"Link analizzati: "
                f"{len(anchors)}"
            )

            for anchor in anchors:

                try:

                    title = self.clean_title(
                        anchor.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    href = (
                        anchor.get(
                            "href"
                        )
                        or ""
                    ).strip()

                    if not title:
                        continue

                    if len(title) < 15:
                        continue

                    link = urljoin(
                        self.BASE_URL,
                        href,
                    )

                    if not self.is_article_link(
                        link
                    ):
                        continue

                    if link in seen_links:
                        continue

                    # --------------------------------------------------
                    # RECUPERO DATI ARTICOLO
                    # --------------------------------------------------

                    (
                        summary,
                        image_url,
                        published,
                        article_text,
                    ) = self.get_article_data(
                        link
                    )

                    # --------------------------------------------------
                    # FILTRO PALERMO
                    # --------------------------------------------------

                    relevant = self.is_palermo_news(
                        title=title,
                        summary=summary,
                        article_text=article_text,
                    )

                    if not relevant:

                        print(
                            "Scartato non-Palermo: "
                            f"{title}"
                        )

                        continue

                    # --------------------------------------------------
                    # DEDUP URL
                    # --------------------------------------------------

                    seen_links.add(
                        link
                    )

                    print(
                        "\n--- NOTIZIA DI MARZIO ---"
                    )

                    print(
                        f"Titolo: {title}"
                    )

                    print(
                        f"Link: {link}"
                    )

                    if summary:

                        print(
                            f"Summary: "
                            f"{summary[:250]}"
                        )

                    if image_url:

                        print(
                            f"Immagine: "
                            f"{image_url}"
                        )

                    if published:

                        print(
                            f"Pubblicata: "
                            f"{published}"
                        )

                    # --------------------------------------------------
                    # NEWS ITEM
                    # --------------------------------------------------

                    items.append(
                        NewsItem(
                            id=link,
                            title=title,
                            link=link,
                            source=self.name,
                            published=published,
                            summary=summary,
                            image_url=image_url,
                        )
                    )

                except Exception as e:

                    print(
                        "Di Marzio: errore "
                        f"analisi link: {e}"
                    )

        print(
            "\n===================="
        )

        print(
            f"Di Marzio: "
            f"{len(items)} notizie Palermo raccolte"
        )

        print(
            "===================="
        )

        return items
