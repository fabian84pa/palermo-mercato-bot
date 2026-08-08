import re


BLACKLIST = (
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
)


def clean_name(name: str) -> str:
    """
    Pulisce il possibile nome trovato.
    """

    name = name.strip()

    if name.casefold() in BLACKLIST:
        return ""

    # Gli insider non possono mai essere giocatori
    if any(insider in name.casefold() for insider in ("matteo moretto", "fabrizio romano", "nico schira", "gianluca di marzio")):
        return ""

    return name


def extract_player(title: str) -> str:
    """
    Estrae un possibile giocatore dal titolo.
    """

    text = title.strip()

    patterns = (

        # dopo parole chiave
        r"(?:di|per|su|segue|seguito da|interessa|piace|obiettivo|arriva)\s+([A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)+)",

        # nomi composti nel titolo
        r"\b([A-ZÀ-Ý][a-zà-ÿ]{2,}\s+[A-ZÀ-Ý][a-zà-ÿ]{2,})\b",
    )


    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            candidate = clean_name(
                match
            )

            if candidate:
                return candidate


    return ""


def format_player(title: str) -> str:
    """
    Formatta il giocatore per Telegram.
    """

    player = extract_player(title)

    if player:
        return (
            f"👤 <b>Giocatore:</b> {player}"
        )

    return ""
