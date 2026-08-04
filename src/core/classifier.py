def classify_news(title: str) -> str:
    """
    Classifica una notizia di calciomercato Palermo.
    """

    text = title.casefold()

    # Ufficialità
    if any(
        keyword in text
        for keyword in (
            "ufficiale",
            "annuncia",
            "annunciato",
            "firma",
            "ha firmato",
            "comunicato",
        )
    ):
        return "🟢 UFFICIALE"

    # Trattative avanzate
    if any(
        keyword in text
        for keyword in (
            "visite mediche",
            "fatta",
            "accordo",
            "accordo raggiunto",
            "vicino",
            "chiuso",
            "arriva",
        )
    ):
        return "🟠 TRATTATIVA AVANZATA"

    # Rumor
    if any(
        keyword in text
        for keyword in (
            "interesse",
            "obiettivo",
            "piace",
            "idea",
            "sondaggio",
            "valuta",
        )
    ):
        return "🟡 RUMOR"

    return "🔵 MERCATO"
