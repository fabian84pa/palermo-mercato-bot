import re


BLACKLIST = {
    "palermo",
    "palermo fc",
    "palermo calcio",
    "serie b",
    "serie a",
    "calciomercato",
    "mercato",
    "tuttomercatoweb",
    "gianluca di marzio",
    "matteo moretto",
    "fabrizio romano",
    "nico schira",
    "nicolò schira",
    "pippo inzaghi",
    "filippo inzaghi",
    "full time",
    "half time",
    "match day",
    "server error",
    "error 500",
    "server",
    "error",
    "that's an error",
    "please try again later",
    "kick off",
    "sub",
    "palermo news",
    "from",
    "show more",
    "source",
    "transfers",
    "trasferimenti",
}


SOURCE_NAMES = {
    "fabrizio romano",
    "matteo moretto",
    "gianluca di marzio",
    "nico schira",
    "nicolò schira",
    "palermo f.c.",
    "palermo fc",
}


def _clean_source_headers(text: str) -> str:
    lines = []

    for line in (text or "").splitlines():

        s = line.strip()

        if not s:
            continue

        low = s.casefold()

        if (
            low in SOURCE_NAMES
            or (
                low.startswith("@")
                and low[1:] in {
                    "fabrizioromano",
                    "mattemoretto",
                    "dimarzio",
                    "nicoschira",
                    "palermofficial",
                }
            )
        ):
            continue

        lines.append(
            line
        )

    return "\n".join(
        lines
    ).strip()


def clean_name(name: str) -> str:

    name = re.sub(
        r"\s+",
        " ",
        (name or "").strip(
            " .,:;!?-"
        ),
    )

    if not name:
        return ""

    if name.casefold() in BLACKLIST:
        return ""

    if name.casefold() in SOURCE_NAMES:
        return ""

    # Evita URL, username e stringhe tecniche.
    if (
        name.startswith("http://")
        or name.startswith("https://")
        or name.startswith("@")
    ):
        return ""

    # Un nome deve avere almeno una lettera.
    if not re.search(
        r"[A-Za-zÀ-ÿ]",
        name,
    ):
        return ""

    return name


def extract_players(
    title: str,
) -> list[str]:

    text = _clean_source_headers(
        title
    )

    if not text:
        return []

    found: list[str] = []

    def add(
        candidate: str,
    ):

        candidate = clean_name(
            candidate
        )

        if not candidate:
            return

        candidate_lower = (
            candidate.casefold()
        )

        # ------------------------------------------------------
        # Squadre / entità che non sono giocatori.
        # ------------------------------------------------------

        if candidate_lower in {
            "zulte waregem",
            "al-ahli",
            "al-hilal",
            "chelsea",
            "lazio",
            "juventus",
            "palermo",
            "atlético madrid",
            "atletico madrid",
            "aston villa",
            "real madrid",
            "barcelona",
            "paris saint-germain",
            "como",
            "fenerbahçe",
            "fenerbahce",
            "inter",
            "milan",
            "roma",
            "napoli",
            "torino",
            "bologna",
            "sassuolo",
            "monza",
            "cagliari",
            "genoa",
            "parma",
        }:
            return

        # Evita parole palesemente non nominali.
        if candidate_lower in {
            "accordo totale",
            "affare fatto",
            "trattativa avanzata",
            "nuovo acquisto",
            "nuovo giocatore",
            "visite mediche",
            "domani",
            "oggi",
            "ieri",
            "profilo",
            "profili",
            "alternative",
            "opzioni",
            "uscita",
            "uscite",
        }:
            return

        if candidate not in found:
            found.append(
                candidate
            )

    # ==========================================================
    # 1) ELENCHI ESPLICITI
    # ==========================================================

    for line in text.splitlines():

        m = re.match(
            r"^\s*[-•]\s*"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}"
            r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})?)"
            r"\s*$",
            line,
        )

        if m:
            add(
                m.group(1)
            )

    if found:
        return found

    # ==========================================================
    # 2) ESAMI / CONDIZIONI / INFORTUNIO
    # ==========================================================

    subject = re.compile(
        r"\b(?:esami|condizioni|infortunio|"
        r"infortunio di|problemi)"
        r"\s+(?:di|del|della)\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+)?)",
        re.I,
    )

    for m in subject.finditer(
        text
    ):
        add(
            m.group(1)
        )

    if found:
        return found

    # ==========================================================
    # 3) LISTE DI PROFILI / NOMI / OPZIONI
    # ==========================================================

    list_patterns = (

        re.compile(
            r"\b(?:profili|nomi|opzioni|alternative)"
            r"\s+(?:di|per)\s+"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})"
            r"(?:\s+e\s+"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}))",
            re.I,
        ),

        re.compile(
            r"\b(?:da)\s+"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})"
            r"\s+a\s+"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b",
            re.I,
        ),
    )

    for pattern in list_patterns:

        for m in pattern.finditer(
            text
        ):

            for group in m.groups():

                if group:
                    add(group)

    if found:
        return found

    # ==========================================================
    # 4) COGNOME SINGOLO IN FRASE DI MERCATO
    # ==========================================================

    single_market = re.compile(
        r"\b(?:trattativa|trattativa in corso|"
        r"offerta|interesse|accordo|cessione|"
        r"acquisto|ingaggio|arrivo|prestito)"
        r"\s+(?:di|per|su)\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b",
        re.I,
    )

    for m in single_market.finditer(
        text
    ):
        add(
            m.group(1)
        )

    if found:
        return found

    # ==========================================================
    # 5) DUE COGNOMI IN CONTESTO DI MERCATO
    # ==========================================================

    pair_single = re.compile(
        r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})"
        r"\s+e\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b"
    )

    if any(
        keyword in text.casefold()
        for keyword in (
            "trattativa",
            "attacco",
            "portiere",
            "profili",
            "uscita",
            "uscite",
            "piani b",
            "alternative",
        )
    ):

        for m in pair_single.finditer(
            text
        ):

            add(
                m.group(1)
            )

            add(
                m.group(2)
            )

    if found:
        return found

    # ==========================================================
    # 6) NOMI COMPOSTI PRIMA DI PREPOSIZIONI DI TRASFERIMENTO
    # ==========================================================

    transfer = re.compile(
        r"\b("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+){1,2}"
        r")\s+"
        r"(?:allo|alla|al|a|nel|nella|dal|dalla|"
        r"verso|per|from|to|joins|join)\b"
    )

    for m in transfer.finditer(
        text
    ):
        add(
            m.group(1)
        )

    if found:
        return found

    # ==========================================================
    # 7) COGNOME DOPO TRATTINO
    # ==========================================================

    single_after_hyphen = re.compile(
        r"-\s*"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’]{2,})"
        r"\s*,\s*"
        r"(?:accordo|trattativa|fatta|vicino|"
        r"ufficiale|annuncia|arriva|firmato|"
        r"deal|agreement)\b",
        re.I,
    )

    for m in single_after_hyphen.finditer(
        text
    ):
        add(
            m.group(1)
        )

    if found:
        return found

    # ==========================================================
    # 8) DUE NOMI COMPLETI
    # ==========================================================

    pair = re.compile(
        r"\b("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+\s+"
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r")\s+e\s+"
        r"("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+\s+"
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r")\b"
    )

    for m in pair.finditer(
        text
    ):

        add(
            m.group(1)
        )

        add(
            m.group(2)
        )

    if found:
        return found

    # ==========================================================
    # 9) NOME ASSOCIATO AD AZIONE
    # ==========================================================

    action = re.compile(
        r"\b("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})?"
        r")\s+"
        r"(?=(?:firma|segna|sigla|realizza|"
        r"sblocca|raddoppio|gol|rete|marcatura|"
        r"scores))",
        re.I,
    )

    for m in action.finditer(
        text
    ):
        add(
            m.group(1)
        )

    if found:
        return found

    # ==========================================================
    # NESSUN FALLBACK GENERICO
    # ==========================================================

    # Meglio non mostrare un falso giocatore.
    return []


def extract_player(
    title: str,
) -> str:

    players = extract_players(
        title
    )

    if not players:
        return ""

    return players[0]


def format_player(
    title: str,
) -> str:

    players = extract_players(
        title
    )

    if not players:
        return ""

    return ", ".join(
        players[:5]
    )
