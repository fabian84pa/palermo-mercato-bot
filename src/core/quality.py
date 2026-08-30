def get_quality_score(title: str, source: str = "") -> int:
    """
    Calcola la qualità/importanza di una notizia di mercato Palermo.

    Il punteggio serve a decidere se una notizia può essere pubblicata.
    Il filtro è volutamente permissivo sulle notizie di mercato valide:
    non dobbiamo perdere un'operazione solo perché il titolo è formulato
    in modo diverso.
    """

    text = (title or "").casefold().strip()
    source_text = (source or "").casefold().strip()

    if not text:
        return 0

    # ----------------------------------------------------------
    # CONTENUTI DA ESCLUDERE
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # BASE SOURCE
    # ----------------------------------------------------------

    trusted_sources = (
        "palermo fc",
        "x calciomercato",
        "gianluca di marzio",
        "tuttomercatoweb",
    )

    score = 30 if any(
        source_name in source_text
        for source_name in trusted_sources
    ) else 10

    # ----------------------------------------------------------
    # UFFICIALE
    # ----------------------------------------------------------

    official_keywords = (
        "ufficiale",
        "annuncia",
        "annunciato",
        "firma",
        "firmato",
        "rinnovo",
        "prolungamento",
        "benvenuto",
        "welcome",
        "official",
        "confirmed",
        "signed",
        "signing",
        "contract signed",
    )

    if any(
        keyword in text
        for keyword in official_keywords
    ):
        return max(
            score + 70,
            100 if "palermo fc" in source_text else score + 70,
        )

    # ----------------------------------------------------------
    # TRATTATIVA AVANZATA
    # ----------------------------------------------------------

    advanced_keywords = (
        "visite mediche",
        "accordo raggiunto",
        "accordo",
        "affare fatto",
        "fatta",
        "fatto",
        "chiuso",
        "chiusa",
        "arriva",
        "arrivato",
        "arrivata",
        "in arrivo",
        "medical",
        "agreement",
        "deal",
        "done deal",
        "here we go",
        "set to join",
        "close to",
    )

    if any(
        keyword in text
        for keyword in advanced_keywords
    ):
        return score + 60

    # ----------------------------------------------------------
    # TRATTATIVA / INTERESSE CONCRETO
    # ----------------------------------------------------------

    concrete_keywords = (
        "obiettivo",
        "trattativa",
        "contatti",
        "offerta",
        "vicino",
        "vicina",
        "intesa",
        "interesse concreto",
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

    if any(
        keyword in text
        for keyword in concrete_keywords
    ):
        return score + 40

    # ----------------------------------------------------------
    # RUMOR
    # ----------------------------------------------------------

    rumor_keywords = (
        "interesse",
        "piace",
        "sondaggio",
        "idea",
        "valuta",
        "valutazione",
        "monitoring",
        "follows",
        "likes",
        "following",
    )

    if any(
        keyword in text
        for keyword in rumor_keywords
    ):
        return score + 15

    # ----------------------------------------------------------
    # NEWS GENERICA DA FONTE AFFIDABILE
    # ----------------------------------------------------------

    # Una notizia proveniente da una fonte affidabile non viene
    # automaticamente persa solo perché il titolo non contiene
    # una delle parole chiave sopra.
    if score >= 30:
        return score

    return score
