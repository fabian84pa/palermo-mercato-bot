from core.provider import Provider
from core.news import NewsItem


class Engine:
    """
    Motore principale del Palermo Mercato Bot.

    Coordina i provider e raccoglie tutte le notizie.
    """

    def __init__(self, providers: list[Provider]):
        self.providers = providers

    def fetch_all(self) -> list[NewsItem]:
        """
        Recupera tutte le notizie da tutti i provider.
        """

        news: list[NewsItem] = []

        for provider in self.providers:
            print(f"Controllo provider: {provider.name}")

            try:
                provider_news = provider.fetch()
                news.extend(provider_news)

            except Exception as exc:
                print(f"Errore nel provider {provider.name}: {exc}")

        return news
