def classify_news(title: str, source: str = "") -> str:
    """
    Classifica una notizia di calciomercato Palermo.
    """

    text = title.casefold()
    source_text = source.casefold()

    # Fonte ufficiale club
    if "palermo fc" in source_text:
        return "🟢 UFFICIALE"

    # Ufficialità dal titolo
    if any(
        keyword in text
        for keyword in (
            "ufficiale",
            "annuncia",
            "annunciato",
            "firma",
            "ha firmato",
            "comunicato",
            "rinnovo",
            "prolungamento",
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
