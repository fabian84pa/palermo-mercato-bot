from core.classifier import classify_news


def get_priority(title: str, source: str = "") -> int:
    """
    Restituisce la priorità della notizia.

    Valore più basso = più importante.
    """

    category = classify_news(
        title,
        source
    )

    priorities = {
        "🟢 UFFICIALE": 1,
        "🟠 TRATTATIVA AVANZATA": 2,
        "🟡 RUMOR": 3,
        "🔵 MERCATO": 4,
    }

    return priorities.get(
        category,
        4
    )
