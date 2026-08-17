from core.classifier import classify_news


def get_priority(title: str, source: str = "") -> int:
    category = classify_news(title, source)
    priorities = {
        "🚑 INFORTUNI": 6,
        "⚽ PARTITA": 5,
        "🟢 UFFICIALE": 4,
        "🟠 TRATTATIVA AVANZATA": 3,
        "🟡 RUMOR": 2,
        "📰 PALERMO NEWS": 1,
    }
    return priorities.get(category, 1)
