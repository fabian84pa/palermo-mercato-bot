def get_quality_score(title: str, source: str = "") -> int:
    """
    Calcola la qualità/importanza di una notizia di mercato Palermo.

    Punteggio più alto = notizia più interessante.
    """

    text = title.casefold()
    source_text = source.casefold()

    score = 0

    # Fonte ufficiale
    if "palermo fc" in source_text:
        score += 100

    # Ufficialità
    if any(
        keyword in text
        for keyword in (
            "ufficiale",
            "annuncia",
            "annunciato",
            "firma",
            "firmato",
            "rinnovo",
            "prolungamento",
        )
    ):
        score += 70

    # Trattativa avanzata
    if any(
        keyword in text
        for keyword in (
            "visite mediche",
            "accordo",
            "accordo raggiunto",
            "fatta",
            "chiuso",
            "arriva",
        )
    ):
        score += 60

    # Interesse concreto
    if any(
        keyword in text
        for keyword in (
            "obiettivo",
            "trattativa",
            "contatti",
            "offerta",
            "vicino",
        )
    ):
        score += 40

    # Rumor deboli
    if any(
        keyword in text
        for keyword in (
            "interesse",
            "piace",
            "sondaggio",
            "idea",
            "valuta",
        )
    ):
        score += 15

    return score
