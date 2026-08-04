from core.news import NewsItem


PALERMO_KEYWORDS = (
    "palermo",
    "palermo fc",
    "rosanero",
    "rosaneri",
    "inzaghi",
)

EXCLUDED_KEYWORDS = (
    "comune di palermo",
    "aeroporto di palermo",
    "provincia di palermo",
    "meteo palermo",
    "cronaca palermo",
)


def is_palermo_news(item: NewsItem) -> bool:
    """
    Restituisce True solo se la notizia riguarda il Palermo FC.
    """

    text = f"{item.title} {item.source}".casefold()

    if any(keyword in text for keyword in EXCLUDED_KEYWORDS):
        return False

    return any(keyword in text for keyword in PALERMO_KEYWORDS)
