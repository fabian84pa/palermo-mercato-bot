def classify_news(title: str, source: str = "") -> str:
    """Classifica una notizia Palermo: mercato, partita, infortuni o news."""
    text = (title or "").casefold()

    injury = (
        "infortunio", "infortunato", "infortunati", "indisponibile",
        "indisponibili", "lesione", "problema muscolare", "problema fisico",
        "recupero", "injury", "injured", "ruled out",
    )
    match = (
        "probabile formazione", "formazione", "formazioni", "convocati",
        "convocato", "match day", "matchday", "partita", "contro il palermo",
        "palermo-", "-palermo", "coppa italia", "calcio d'inizio",
        "prepartita", "post partita", "post-partita", "risultato",
        "amichevole", "starting xi", "line-up", "lineup",
    )
    official = (
        "ufficiale", "annuncia", "annunciato", "ha firmato", "firmato",
        "rinnovo", "prolungamento", "nuovo acquisto", "nuovo giocatore",
        "official", "confirmed", "signed", "signing", "contract signed",
    )
    advanced = (
        "visite mediche", "accordo raggiunto", "accordo", "affare fatto",
        "operazione chiusa", "chiuso", "fatta", "vicino", "intesa",
        "agreement", "done deal", "medical", "here we go", "close to",
        "set to join",
    )
    rumor = (
        "obiettivo", "trattativa", "contatti", "offerta", "interesse",
        "interessato", "piace", "sondaggio", "idea", "valuta",
        "target", "talks", "in talks", "interest", "interested",
        "proposal", "bid", "offer", "monitoring",
    )

    if any(k in text for k in injury):
        return "🚑 INFORTUNI"
    if any(k in text for k in match):
        return "⚽ PARTITA"
    if any(k in text for k in official):
        return "🟢 UFFICIALE"
    if any(k in text for k in advanced):
        return "🟠 TRATTATIVA AVANZATA"
    if any(k in text for k in rumor):
        return "🟡 RUMOR"
    return "📰 PALERMO NEWS"
