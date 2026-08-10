from core.classifier import classify_news


def get_priority(title: str, source: str = "") -> int:
    """Valore più basso = più importante."""
    category = classify_news(title, source)

    priorities = {
        "🟢 UFFICIALE": 1,
        "🟠 TRATTATIVA AVANZATA": 2,
        "🚑 INFORTUNI": 2,
        "⚽ PARTITA": 3,
        "🟡 RUMOR": 3,
        "📰 PALERMO NEWS": 4,
    }

    return priorities.get(category, 4)
