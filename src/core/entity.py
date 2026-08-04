import re


def extract_player(title: str) -> str:
    """
    Estrae un possibile nome giocatore dal titolo della notizia.
    """

    text = title.strip()

    # Rimuove prefissi comuni
    prefixes = (
        "palermo,",
        "palermo:",
        "palermo fc,",
        "palermo fc:",
    )

    for prefix in prefixes:
        if text.casefold().startswith(prefix):
            text = text[len(prefix):].strip()

    # Parole che indicano la presenza di un nome dopo
    patterns = (
        r"(?:di|per|su|per il ritorno di|arriva|preso|firma)\s+([A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)+)",
        r"([A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)+)"
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            candidate = match.group(1).strip()

            # Evita falsi positivi comuni
            blacklist = (
                "Serie B",
                "Palermo Calcio",
                "Tutto Mercato",
                "Gianluca Di",
            )

            if candidate not in blacklist:
                return candidate

    return ""


def format_player(title: str) -> str:

    player = extract_player(title)

    if player:
        return f"👤 <b>Giocatore:</b> {player}"

    return ""
