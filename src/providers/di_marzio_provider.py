from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from core.news import NewsItem
from core.provider import Provider


class DiMarzioProvider(Provider):
    """Recupera soltanto notizie di mercato con un legame verificabile al Palermo."""

    BASE_URL = "https://www.gianlucadimarzio.com"

    NEWS_URLS = (
        "https://www.gianlucadimarzio.com/calciomercato/",
        "https://www.gianlucadimarzio.com/",
    )

    # Questi riferimenti sono sufficienti soltanto se appaiono nel titolo
    # o nella descrizione editoriale: non nel testo libero della pagina,
    # che può contenere menu e articoli correlati.
    PALERMO_MARKERS = (
        "palermo",
        "palermo fc",
        "palermo calcio",
        "rosanero",
        "rosaneri",
    )

    # Profili effettivamente monitorati dal bot. Sono divisi da Inzaghi:
    # il suo cognome, molto comune nelle notizie di calcio, non può essere
    # usato come unico criterio di ammissione.
    MONITORED_PEOPLE = (
        "pohjanpalo",
        "gabrielloni",
        "almena",
        "osti",
        "strefezza",
        "brunori",
        "perin",
        "sportiello",
        "semper",
        "audero",
        "thiam",
        "kostic",
    )

    INZAGHI_MARKERS = (
        "filippo inzaghi",
        "pippo inzaghi",
        "inzaghi",
    )

    MARKET_MARKERS = (
        "calciomercato",
        "mercato",
        "trattativa",
        "trattative",
        "accordo",
        "accordi",
        "offerta",
        "offerte",
        "interesse",
        "interessa",
        "acquisto",
        "acquistato",
        "acquista",
        "cessione",
        "cessioni",
        "ceduto",
        "ceduta",
        "prestito",
        "riscatto",
        "firma",
        "firmato",
        "contratto",
        "rinnovo",
        "rinnovato",
        "arriva",
        "in arrivo",
        "ufficiale",
        "ufficialmente",
        "ingaggia",
        "ingaggiato",
        "nuovo acquisto",
        "nuovo giocatore",
        "visite mediche",
        "accordo raggiunto",
        "here we go",
    )

    EXCLUDED_PATH_PARTS = (
        "/calciomercato",
        "/caffe-di-marzio",
        "/interviste-e-storie",
        "/video",
        "/tag/",
        "/categoria/",
        "/author/",
        "/search",
        "/login",
        "/page/",
    )

    # Sono esclusioni assolute: anche una citazione al Palermo non rende
    # utile per questo bot una partita, una convocazione o una designazione.
    EXCLUDED_EDITORIAL_MARKERS = (
        "formazioni ufficiali",
        "formazione ufficiale",
        "probabili formazioni",
        "designazioni arbitrali",
        "designazione arbitrale",
        "arbitri",
        "dove vedere",
        "in tv e streaming",
        "diretta testuale",
        "live",
        "risultati",
        "classifica",
        "calendario",
        "convocati",
        "nazionale",
        "italia:",
        "italia ",
    )

    # Non sono un blocco se la stessa notizia ha gia' superato i criteri
    # Palermo/mercato; evitano invece che una news generica di altri club
    # passi grazie a un nome intercettato per errore nel testo.
    OTHER_CLUB_MARKERS = (
        "inter",
        "milan",
        "juventus",
        "roma",
        "napoli",
        "lazio",
        "atalanta",
        "fiorentina",
        "torino",
        "genoa",
        "como",
        "lecce",
        "parma",
        "monza",
        "bologna",
        "sassuolo",
        "udinese",
        "cagliari",
        "cremonese",
        "venezia",
        "frosinone",
        "pisa",
        "catanzaro",
        "empoli",
        "sampdoria",
        "bari",
        "salernitana",
    )

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
    }

    TIMEOUT = 30

    @property
    def name(self) -> str:
        return "Gianluca Di Marzio"

    def get_page(self, url: str):
        response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def get_meta(soup: BeautifulSoup, *, name: str = None, prop: str = None) -> str:
        attrs = {}
        if name:
            attrs["name"] = name
        if prop:
            attrs["property"] = prop

        tag = soup.find("meta", attrs=attrs)
        return (tag.get("content") or "").strip() if tag else ""

    @staticmethod
    def get_article_text(soup: BeautifulSoup) -> str:
        """Estrae il corpo editoriale, senza menu e contenuti correlati."""
        selectors = (
            "article",
            "[itemprop='articleBody']",
            ".article-body",
            ".article-content",
            ".post-content",
            ".entry-content",
        )
        for selector in selectors:
            nodes = soup.select(selector)
            text = " ".join(node.get_text(" ", strip=True) for node in nodes)
            if text:
                return text
        return ""

    def get_article_data(self, link: str):
        try:
            soup = self.get_page(link)
            summary = (
                self.get_meta(soup, name="description")
                or self.get_meta(soup, prop="og:description")
            )
            image_url = self.get_meta(soup, prop="og:image")
            published = (
                self.get_meta(soup, prop="article:published_time")
                or self.get_meta(soup, name="date")
            )
            if not published:
                time_tag = soup.find("time")
                if time_tag:
                    published = time_tag.get("datetime") or time_tag.get_text(
                        " ", strip=True
                    )

            return summary, image_url, published, self.get_article_text(soup)
        except Exception as error:
            print(f"Di Marzio: errore articolo {link}: {error}")
            return "", "", "", ""

    @staticmethod
    def clean_title(title: str) -> str:
        return " ".join((title or "").split()).strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        return " ".join((text or "").casefold().split())

    @staticmethod
    def contains_any(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    def is_article_link(self, link: str) -> bool:
        if not link.startswith(self.BASE_URL):
            return False

        path = link.removeprefix(self.BASE_URL).casefold()
        if path.rstrip("/") in ("", "/calciomercato"):
            return False
        return not self.contains_any(path, self.EXCLUDED_PATH_PARTS)

    def is_palermo_news(
        self,
        title: str,
        summary: str = "",
        article_text: str = "",
    ) -> bool:
        """Applica il filtro prima di creare il NewsItem.

        Il corpo puo' soltanto confermare un profilo gia' individuato nel
        titolo: da solo non viene mai usato per far passare una notizia.
        """
        normalized_title = self.normalize_text(title)
        normalized_summary = self.normalize_text(summary)
        normalized_body = self.normalize_text(article_text)
        editorial_text = f"{normalized_title} {normalized_summary}".strip()

        if self.contains_any(editorial_text, self.EXCLUDED_EDITORIAL_MARKERS):
            return False

        has_palermo = self.contains_any(editorial_text, self.PALERMO_MARKERS)
        has_market = self.contains_any(editorial_text, self.MARKET_MARKERS)
        title_has_person = self.contains_any(
            normalized_title, self.MONITORED_PEOPLE
        )
        title_has_inzaghi = self.contains_any(normalized_title, self.INZAGHI_MARKERS)

        # Un Palermo/Rosanero esplicito nell'anteprima e' un collegamento
        # concreto. Per Inzaghi serve in aggiunta il contesto mercato.
        if has_palermo:
            if title_has_inzaghi and not has_market:
                return False
            return True

        # Un profilo monitorato e' ammesso soltanto se e' il soggetto del
        # titolo e l'anteprima parla di mercato. Il corpo e' una conferma
        # aggiuntiva, non una scorciatoia per notizie di altri club.
        if title_has_person and has_market:
            return True

        # Inzaghi senza Palermo esplicito non basta mai, neppure quando
        # l'articolo parla di mercato.
        if title_has_inzaghi:
            return False

        # La lista rende esplicito il rifiuto delle news generiche su altri
        # club; tutte le altre news senza criteri positivi sono rifiutate.
        if self.contains_any(editorial_text, self.OTHER_CLUB_MARKERS):
            return False

        # article_text e' deliberatamente inutilizzato come criterio
        # positivo: puo' contenere riferimenti casuali o articoli correlati.
        _ = normalized_body
        return False

    def fetch(self) -> list[NewsItem]:
        items = []
        seen_links = set()

        print("\n====================")
        print("CONTROLLO PROVIDER: Gianluca Di Marzio")
        print("====================")

        for news_url in self.NEWS_URLS:
            print(f"Pagina Di Marzio: {news_url}")
            try:
                soup = self.get_page(news_url)
            except Exception as error:
                print(f"Di Marzio: errore pagina {news_url}: {error}")
                continue

            anchors = soup.find_all("a", href=True)
            print(f"Link analizzati: {len(anchors)}")

            for anchor in anchors:
                try:
                    title = self.clean_title(anchor.get_text(" ", strip=True))
                    href = (anchor.get("href") or "").strip()
                    if not title or len(title) < 15:
                        continue

                    link = urljoin(self.BASE_URL, href)
                    if not self.is_article_link(link) or link in seen_links:
                        continue

                    summary, image_url, published, article_text = self.get_article_data(link)
                    if not self.is_palermo_news(title, summary, article_text):
                        print(f"Scartato non-Palermo: {title}")
                        continue

                    seen_links.add(link)
                    print("\n--- NOTIZIA DI MARZIO ---")
                    print(f"Titolo: {title}")
                    print(f"Link: {link}")
                    if summary:
                        print(f"Summary: {summary[:250]}")
                    if image_url:
                        print(f"Immagine: {image_url}")

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
                except Exception as error:
                    print(f"Di Marzio: errore analisi link: {error}")

        print("\n====================")
        print(f"Di Marzio: {len(items)} notizie Palermo raccolte")
        print("====================")
        return items
