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

        lines.append(line)

    return "\n".join(lines).strip()


def clean_name(name: str) -> str:

    name = re.sub(
        r"\s+",
        " ",
        (name or "").strip(" .,:;!?-")
    )

    if not name:
        return ""

    if name.casefold() in BLACKLIST:
        return ""

    if name.casefold() in SOURCE_NAMES:
        return ""

    return name


def extract_players(title: str) -> list[str]:

    text = _clean_source_headers(title)

    if not text:
        return []

    found: list[str] = []

    def add(candidate: str):

        candidate = clean_name(candidate)

        if not candidate:
            return

        # Non è un giocatore se è chiaramente una squadra/entità comune.
        if candidate.casefold() in {
            "zulte waregem",
            "al-ahli",
            "al-hilal",
            "chelsea",
            "lazio",
            "juventus",
            "palermo",
            "atlético madrid",
            "aston villa",
            "real madrid",
            "barcelona",
            "paris saint-germain",
        }:
            return

        if candidate not in found:
            found.append(candidate)

    # 1) Elenchi espliciti:
    # - Blin
    # - Gyasi
    # - Brunori
    for line in text.splitlines():

        m = re.match(
            r"^\s*[-•]\s*"
            r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}"
            r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})?)"
            r"\s*$",
            line
        )

        if m:
            add(m.group(1))

    # Se abbiamo trovato un elenco, quello è il dato più affidabile.
    if found:
        return found

    # 2) Giocatore oggetto di esami/condizioni/infortunio:
    # "esami di Joronen"
    subject = re.compile(
        r"\b(?:esami|condizioni|infortunio|infortunio di|problemi)"
        r"\s+(?:di|del|della)\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+)?)",
        re.I,
    )

    for m in subject.finditer(text):
        add(m.group(1))

    # 3) Liste di giocatori nella stessa frase:
    # "profili di Sportiello e Semper"
    # "da Pinamonti a Piccoli"
    #
    # I cognomi singoli sono ammessi solo quando la frase
    # contiene marcatori espliciti di giocatori/profili/opzioni.
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

        for m in pattern.finditer(text):

            for group in m.groups():

                if group:
                    add(group)

    if found:
        return found

    # 4) Cognome singolo in frasi di mercato:
    # "trattativa di Perin"
    # "offerta per Perin"
    # "interesse per Pinamonti"
    single_market = re.compile(
        r"\b(?:trattativa|trattativa in corso|offerta|interesse|"
        r"accordo|cessione|acquisto|ingaggio|arrivo|prestito)"
        r"\s+(?:di|per|su)\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b",
        re.I,
    )

    for m in single_market.finditer(text):
        add(m.group(1))

    if found:
        return found

    # 5) Cognomi collegati da "e" in contesti di mercato.
    pair_single = re.compile(
        r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})"
        r"\s+e\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b"
    )

    if any(
        k in text.casefold()
        for k in (
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

        for m in pair_single.finditer(text):

            add(m.group(1))
            add(m.group(2))

    if found:
        return found

    # 6) Nomi composti prima di una tipica preposizione
    # di trasferimento.
    transfer = re.compile(
        r"\b("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+){1,2}"
        r")\s+"
        r"(?:allo|alla|al|a|nel|nella|dal|dalla|verso|"
        r"per|from|to|joins|join)\b"
    )

    for m in transfer.finditer(text):
        add(m.group(1))

    if found:
        return found

    # 7) Cognome singolo in formati tipo:
    # "Fenerbahçe-Lukaku, accordo totale"
    single_after_hyphen = re.compile(
        r"-\s*"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’]{2,})"
        r"\s*,\s*"
        r"(?:accordo|trattativa|fatta|vicino|ufficiale|"
        r"annuncia|arriva|firmato|deal|agreement)\b",
        re.I,
    )

    for m in single_after_hyphen.finditer(text):
        add(m.group(1))

    if found:
        return found

    # 8) Più giocatori in una frase:
    # "Andrea Pinamonti e Roberto Piccoli..."
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

    for m in pair.finditer(text):

        add(m.group(1))
        add(m.group(2))

    if found:
        return found

    # 9) Cognome/nome associato a un'azione di gioco.
    #
    # Evita di prendere frasi casuali (es. "GIOELEEEEE")
    # come nome del giocatore.
    action = re.compile(
        r"\b("
        r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}"
        r"(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})?"
        r")\s+"
        r"(?=(?:firma|segna|sigla|realizza|sblocca|"
        r"raddoppio|gol|rete|marcatura|scores))",
        re.I,
    )

    for m in action.finditer(text):
        add(m.group(1))

    if found:
        return found

    # Nessun fallback generico:
    # meglio non mostrare un giocatore che inventarne uno
    # da testo, errori HTTP o frasi dei tifosi.
    return []


def extract_player(title: str) -> str:

    players = extract_players(title)

    return players[0] if players else ""


def format_player(title: str) -> str:

    players = extract_players(title)

    if not players:
        return ""

    return ", ".join(players[:5])
