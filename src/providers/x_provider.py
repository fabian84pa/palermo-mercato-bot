from pathlib import Path
import hashlib
import json
import re
import time
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

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

    # Host RSS-Bridge pubblici.
    # Vengono provati in ordine fino a quando uno restituisce
    # una timeline valida.
    RSS_BRIDGES = (
        "https://rss-bridge.org/bridge01/",
        "https://rssbridge.eris.cc/",
        "https://rssbridge.sciunto.org/",
        "https://rss-bridge.brihx.fr/",
        "https://www.bridge.mergis.net/",
        "https://bridge.narreal.com.br/",
        "https://rss-bridge.qth.fr/",
        "https://rss-bridge.nomadic.name/",
        "https://rss-bridge.noh.am/",
        "https://bridge.folk.zone/",
        "https://rss-bridge.daemonratte.net/",
    )

    PALERMO_CONTEXT = (
        "palermo",
        "palermo fc",
        "palermofficial",
        "rosanero",
        "rosaneri",
        "aquile",
        "almena",
        "al-qadisiyya",
        "al-qadisiyah",
        "al qadisiyya",
        "osti",
        "inzaghi",
        "strefezza",
        "pohjanpalo",
    )

    # Termini che possono identificare un post Palermo
    # anche quando il nome Palermo non compare esplicitamente.
    PALERMO_PLAYER_CONTEXT = (
        "almena",
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

        text = (
            text
            or ""
        )

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
    # HTML CLEAN
    # ==========================================================

    def clean_html(
        self,
        text
    ):

        if not text:

            return ""

        text = unescape(
            text
        )

        # Rimuove immagini HTML.
        text = re.sub(
            r"<img[^>]*>",
            " ",
            text,
            flags=re.I
        )

        # Link HTML:
        # conserva il testo ma non il tag.
        text = re.sub(
            r"<a[^>]*>(.*?)</a>",
            r"\1",
            text,
            flags=re.I | re.S
        )

        # Tutti gli altri tag.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text
        )

        text = text.replace(
            "\\n",
            "\n"
        )

        text = text.replace(
            "\r\n",
            "\n"
        )

        text = text.replace(
            "\r",
            "\n"
        )

        # Elimina righe vuote eccessive.
        lines = []

        for line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                line
            ).strip()

            if line:

                lines.append(
                    line
                )

        return "\n".join(
            lines
        ).strip()

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
    # PALERMO FILTER
    # ==========================================================

    def is_market_palermo_context(
        self,
        text
    ):

        normalized = (
            text
            or ""
        ).casefold()

        return any(
            word in normalized
            for word in self.PALERMO_CONTEXT
        )

    # ==========================================================
    # PALERMO OFFICIAL
    # ==========================================================

    def is_market_post_official(
        self,
        text
    ):

        normalized = (
            text
            or ""
        ).casefold()

        excluded = (
            "match day",
            "matchday",
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
    # RELEVANCE
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
    # XML HELPERS
    # ==========================================================

    def _local_name(
        self,
        tag
    ):

        if not tag:

            return ""

        if "}" in tag:

            return tag.rsplit(
                "}",
                1
            )[1]

        return tag

    def _find_text(
        self,
        element,
        names
    ):

        for child in element.iter():

            if (
                self._local_name(
                    child.tag
                ).casefold()
                in names
            ):

                if child.text:

                    return child.text.strip()

        return ""

    def _find_link(
        self,
        element
    ):

        # Atom <link href="..."/>
        for child in element.iter():

            if (
                self._local_name(
                    child.tag
                ).casefold()
                == "link"
            ):

                href = child.attrib.get(
                    "href",
                    ""
                )

                if href:

                    return href

                if child.text:

                    return child.text.strip()

        return ""

    def _find_image(
        self,
        element,
        content=""
    ):

        # media:content / media:thumbnail
        for child in element.iter():

            name = self._local_name(
                child.tag
            ).casefold()

            if name in (
                "content",
                "thumbnail",
                "enclosure",
            ):

                url = (
                    child.attrib.get(
                        "url"
                    )
                    or child.attrib.get(
                        "href"
                    )
                )

                if (
                    url
                    and url.startswith(
                        "http"
                    )
                ):

                    return url

        # Cerca eventuali immagini nell'HTML.
        if content:

            match = re.search(
                r'<img[^>]+src=["\']([^"\']+)',
                content,
                flags=re.I
            )

            if match:

                return match.group(1)

        return ""

    # ==========================================================
    # FEED PARSER
    # ==========================================================

    def parse_feed(
        self,
        xml_data,
        source
    ):

        posts = []

        try:

            root = ET.fromstring(
                xml_data
            )

        except Exception as e:

            print(
                f"Errore parsing RSS @{source}: {e}"
            )

            return posts

        entries = []

        for element in root.iter():

            name = self._local_name(
                element.tag
            ).casefold()

            if name in (
                "item",
                "entry",
            ):

                entries.append(
                    element
                )

        for entry in entries:

            try:

                title = self._find_text(
                    entry,
                    {
                        "title"
                    }
                )

                description = (
                    self._find_text(
                        entry,
                        {
                            "description",
                            "summary",
                            "content",
                        }
                    )
                )

                link = self._find_link(
                    entry
                )

                published = (
                    self._find_text(
                        entry,
                        {
                            "pubdate",
                            "published",
                            "updated",
                        }
                    )
                )

                raw_content = (
                    title
                    + "\n"
                    + description
                )

                image_url = (
                    self._find_image(
                        entry,
                        description
                    )
                )

                text = self.clean_html(
                    description
                    or title
                )

                if not text:

                    text = self.clean_html(
                        title
                    )

                if not text:

                    continue

                # Se il feed mette il titolo
                # separatamente dalla descrizione,
                # utilizziamo la descrizione come testo
                # principale quando contiene più informazioni.
                if (
                    title
                    and description
                    and len(
                        self.clean_html(
                            description
                        )
                    ) < 20
                ):

                    text = self.clean_html(
                        title
                    )

                posts.append(
                    {
                        "text": text,
                        "title": self.clean_html(
                            title
                        ),
                        "link": link,
                        "published": published,
                        "image_url": image_url,
                    }
                )

            except Exception as e:

                print(
                    f"Errore parsing item @{source}: {e}"
                )

        return posts

    # ==========================================================
    # RSS REQUEST
    # ==========================================================

    def fetch_rss(
        self,
        base_url,
        source
    ):

        params = {
            "action": "display",
            "bridge": "Twitter",
            "context": "By username",
            "u": source,
            "format": "Atom",
            "norep": "1",
            "noretweet": "1",
            "nopinned": "1",
        }

        url = (
            base_url.rstrip("/")
            + "/?"
            + urlencode(
                params
            )
        )

        print(
            f"RSS X: @{source} -> {base_url}"
        )

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; PalermoMercatoBot/1.0)"
                ),
                "Accept": (
                    "application/atom+xml,"
                    "application/rss+xml,"
                    "application/xml,"
                    "text/xml,*/*"
                ),
            }
        )

        try:

            with urlopen(
                request,
                timeout=30
            ) as response:

                data = response.read()

            if not data:

                return []

            posts = self.parse_feed(
                data,
                source
            )

            print(
                f"RSS X: @{source} -> "
                f"{len(posts)} post"
            )

            return posts

        except HTTPError as e:

            print(
                f"RSS X HTTP @{source}: "
                f"{e.code}"
            )

        except URLError as e:

            print(
                f"RSS X URL @{source}: "
                f"{e.reason}"
            )

        except Exception as e:

            print(
                f"RSS X errore @{source}: {e}"
            )

        return []

    # ==========================================================
    # RACCOLTA ACCOUNT
    # ==========================================================

    def collect_posts(
        self,
        source
    ):

        # Deduplica anche tra diversi bridge.
        collected = []

        seen = set()

        for base_url in self.RSS_BRIDGES:

            posts = self.fetch_rss(
                base_url,
                source
            )

            for post in posts:

                text = post.get(
                    "text",
                    ""
                )

                link = post.get(
                    "link",
                    ""
                )

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

                collected.append(
                    post
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

            # Se un bridge funziona e restituisce
            # dati, non bombardiamo tutti gli altri host.
            if posts:

                break

            time.sleep(
                0.5
            )

        print(
            f"Totale raccolti @{source}: "
            f"{len(collected)}"
        )

        return collected

    # ==========================================================
    # MERGE
    # ==========================================================

    def merge_posts(
        self,
        posts
    ):

        merged = []

        seen = set()

        for post in posts:

            text = post.get(
                "text",
                ""
            )

            link = post.get(
                "link",
                ""
            )

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
    # FETCH
    # ==========================================================

    def fetch(self):

        items = []

        print(
            "\n===================="
        )

        print(
            "CONTROLLO X - RSS AUTOMATICO"
        )

        print(
            "Nessun login X richiesto."
        )

        print(
            "===================="
        )

        for source in self.SOURCES:

            print(
                "\n===================="
            )

            print(
                f"CONTROLLO X: @{source}"
            )

            try:

                posts = (
                    self.collect_posts(
                        source
                    )
                )

                posts = (
                    self.merge_posts(
                        posts
                    )
                )

                print(
                    f"Post dopo dedup "
                    f"@{source}: "
                    f"{len(posts)}"
                )

                for post in posts:

                    text = post.get(
                        "text",
                        ""
                    )

                    link = post.get(
                        "link",
                        ""
                    )

                    published = post.get(
                        "published",
                        ""
                    )

                    image_url = post.get(
                        "image_url",
                        ""
                    )

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

                    # Titolo:
                    # preferiamo il titolo RSS se sensato,
                    # altrimenti usiamo il testo.
                    title = post.get(
                        "title",
                        ""
                    )

                    title = self.clean_html(
                        title
                    )

                    if not title:

                        title = text[:120]

                    items.append(
                        NewsItem(
                            id=item_id,
                            title=title[:120],
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
