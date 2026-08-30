def classify_news(title: str, source: str = "") -> str:
    """
    Classifica una notizia Palermo.

    Ordine:
    1. Infortuni
    2. Partita
    3. Ufficiale
    4. Trattativa avanzata
    5. Rumor
    6. Palermo News
    """

    text = (title or "").casefold().strip()

    # ==========================================================
    # INFORTUNI
    # ==========================================================

    injury = (
        "infortunio",
        "infortunato",
        "infortunati",
        "indisponibile",
        "indisponibili",
        "lesione",
        "problema muscolare",
        "problema fisico",
        "problemi fisici",
        "injury",
        "injured",
        "ruled out",
        "out per infortunio",
        "salta per infortunio",
    )

    # ==========================================================
    # PARTITA
    # ==========================================================

    match = (
        "probabile formazione",
        "formazione",
        "formazioni",
        "convocati",
        "convocato",
        "convocazione",
        "match day",
        "matchday",
        "partita",
        "contro il palermo",
        "contro la palermo",
        "palermo-",
        "-palermo",
        "coppa italia",
        "calcio d'inizio",
        "calcio d’inizio",
        "prepartita",
        "pre-partita",
        "post partita",
        "post-partita",
        "risultato",
        "amichevole",
        "starting xi",
        "line-up",
        "lineup",
        "full time",
        "half time",
        "half-time",
        "intervallo",
        "kick off",
        "kick-off",
        "inizia",
        "inizio",
        "sostituzione",
        "minuti di recupero",
        "tempo di recupero",
        "finisce",
        "vince",
        "vittoria",
        "sconfitta",
        "pareggio",
        "finale",
    )

    # ==========================================================
    # UFFICIALE
    # ==========================================================

    official = (
        "ufficiale",
        "ufficialmente",
        "annuncia",
        "annunciato",
        "annunciata",
        "ha firmato",
        "firmato",
        "firmata",
        "firma",
        "rinnovo",
        "rinnovato",
        "rinnovata",
        "prolungamento",
        "nuovo acquisto",
        "nuovo giocatore",
        "nuova giocatrice",
        "benvenuto",
        "benvenuta",
        "welcome",
        "official",
        "confirmed",
        "signed",
        "signing",
        "contract signed",
    )

    # ==========================================================
    # TRATTATIVA AVANZATA
    # ==========================================================

    advanced = (
        "visite mediche",
        "visita medica",
        "accordo raggiunto",
        "accordo totale",
        "accordo",
        "affare fatto",
        "operazione chiusa",
        "operazione conclusa",
        "chiuso",
        "chiusa",
        "fatta",
        "fatto",
        "intesa raggiunta",
        "intesa",
        "vicino",
        "vicina",
        "in arrivo",
        "arriva",
        "arrivato",
        "arrivata",
        "medical",
        "agreement",
        "done deal",
        "here we go",
        "close to",
        "set to join",
    )

    # ==========================================================
    # RUMOR / TRATTATIVA
    # ==========================================================

    rumor = (
        "obiettivo",
        "trattativa",
        "contatti",
        "offerta",
        "interesse",
        "interesse concreto",
        "interessato",
        "interessata",
        "piace",
        "sondaggio",
        "idea",
        "valuta",
        "valutazione",
        "target",
        "talks",
        "in talks",
        "interest",
        "interested",
        "proposal",
        "bid",
        "offer",
        "monitoring",
        "profili",
        "profilo",
        "in corsa",
        "opzione",
        "possibile",
        "possibile arrivo",
        "avanzano i profili",
    )

    # ==========================================================
    # ORDINE DI CLASSIFICAZIONE
    # ==========================================================

    if any(
        keyword in text
        for keyword in injury
    ):
        return "🚑 INFORTUNI"

    if any(
        keyword in text
        for keyword in match
    ):
        return "⚽ PARTITA"

    if any(
        keyword in text
        for keyword in official
    ):
        return "🟢 UFFICIALE"

    if any(
        keyword in text
        for keyword in advanced
    ):
        return "🟠 TRATTATIVA AVANZATA"

    if any(
        keyword in text
        for keyword in rumor
    ):
        return "🟡 RUMOR"

    return "📰 PALERMO NEWS"
