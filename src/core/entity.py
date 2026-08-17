import re


BLACKLIST = {
    "palermo", "palermo fc", "palermo calcio", "serie b", "serie a",
    "calciomercato", "mercato", "tuttomercatoweb", "gianluca di marzio",
    "matteo moretto", "fabrizio romano", "nico schira", "nicolò schira",
    "pippo inzaghi", "filippo inzaghi", "full time", "match day",
}

SOURCE_NAMES = {
    "fabrizio romano", "matteo moretto", "gianluca di marzio",
    "nico schira", "nicolò schira", "palermo f.c.", "palermo fc",
}


def _clean_source_headers(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        low = s.casefold()
        if low in SOURCE_NAMES or low.startswith("@") and low[1:] in {
            "fabrizioromano", "mattemoretto", "dimarzio", "nicoschira", "palermofficial"
        }:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "").strip(" .,:;!?-"))
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
            "zulte waregem", "al-ahli", "al-hilal", "chelsea", "lazio",
            "juventus", "palermo", "atlético madrid", "aston villa",
            "real madrid", "barcelona", "paris saint-germain",
        }:
            return
        if candidate not in found:
            found.append(candidate)

    # 1) Elenchi espliciti: - Blin / - Gyasi / - Brunori
    for line in text.splitlines():
        m = re.match(r"^\s*[-•]\s*([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})?)\s*$", line)
        if m:
            add(m.group(1))

    # Se abbiamo trovato un elenco, quello è il dato più affidabile.
    if found:
        return found

    # 2) Nomi composti prima di una tipica preposizione di trasferimento.
    transfer = re.compile(
        r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+){1,2})\s+"
        r"(?:allo|alla|al|a|nel|nella|dal|dalla|verso|per|from|to|joins|join)\b"
    )
    for m in transfer.finditer(text):
        add(m.group(1))

    if found:
        return found

    # 3) Cognome singolo in formati tipo "Fenerbahçe-Lukaku, accordo totale".
    single_after_hyphen = re.compile(
        r"-\s*([A-ZÀ-Ý][A-Za-zÀ-ÿ'’]{2,})\s*,\s*"
        r"(?:accordo|trattativa|fatta|vicino|ufficiale|annuncia|arriva|firmato|deal|agreement)\b",
        re.I,
    )
    for m in single_after_hyphen.finditer(text):
        add(m.group(1))

    if found:
        return found

    # 3) Più giocatori in una frase: "Andrea Pinamonti e Roberto Piccoli..."
    pair = re.compile(
        r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+)\s+e\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]+)\b"
    )
    for m in pair.finditer(text):
        add(m.group(1)); add(m.group(2))

    if found:
        return found

    # 5) Ultimo fallback: due parole capitalizzate, ma saltando nomi noti di fonti/allenatori.
    generic = re.compile(r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,}\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.-]{2,})\b")
    for m in generic.finditer(text):
        candidate = m.group(1)
        if candidate.casefold() in BLACKLIST or candidate.casefold() in SOURCE_NAMES:
            continue
        add(candidate)
        if len(found) >= 3:
            break

    return found


def extract_player(title: str) -> str:
    players = extract_players(title)
    return players[0] if players else ""


def format_player(title: str) -> str:
    players = extract_players(title)
    if not players:
        return ""
    return ", ".join(players[:5])
