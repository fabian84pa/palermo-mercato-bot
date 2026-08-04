from core.news import NewsItem
from core.provider import Provider


class DiMarzioProvider(Provider):
    @property
    def name(self) -> str:
        return "Gianluca Di Marzio"

    def fetch(self) -> list[NewsItem]:
        """
        Provider temporaneo.
        Nel prossimo step leggeremo davvero il feed RSS.
        """
        return []
