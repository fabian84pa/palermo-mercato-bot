def get_quality_score(title: str, source: str = "") -> int:
    """
    Calcola la qualità/importanza di una notizia di mercato Palermo.
    """

    text = title.casefold()
    source_text = source.casefold()

    score = 0


    excluded_keywords = (
        "biglietto",
        "biglietti",
        "ticket",
        "store",
        "shop",
        "community",
        "sponsor",
        "marketing",
        "evento",
        "eventi",
        "academy",
        "junior",
        "codice etico",
    )


    if any(
        keyword in text
        for keyword in excluded_keywords
    ):
        return 0



    # Fonti mercato affidabili
    if any(
        source_name in source_text
        for source_name in (
            "palermo fc",
            "x calciomercato",
            "gianluca di marzio",
            "tuttomercatoweb",
        )
    ):
        score += 30



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

            # inglese
            "official",
            "confirmed",
            "signed",
            "signing",
            "contract signed",
        )
    ):
        score += 70



    # Trattative avanzate
    if any(
        keyword in text
        for keyword in (
            "visite mediche",
            "accordo",
            "accordo raggiunto",
            "fatta",
            "chiuso",
            "arriva",

            # inglese
            "agreement",
            "deal",
            "done deal",
            "medical",
            "here we go",
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

            # inglese
            "target",
            "talks",
            "in talks",
            "interest",
            "interested",
            "proposal",
            "bid",
            "offer",
            "close",
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

            # inglese
            "likes",
            "monitoring",
            "follows",
        )
    ):
        score += 15


    return score
