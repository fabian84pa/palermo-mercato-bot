from abc import ABC, abstractmethod

from core.news import NewsItem


class Provider(ABC):
    """
    Classe base per tutti i provider.

    Ogni provider (Di Marzio, TMW, Palermo FC, ecc.)
    dovrà ereditare da questa classe.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nome del provider.
        """
        pass

    @abstractmethod
    def fetch(self) -> list[NewsItem]:
        """
        Recupera le notizie.

        Deve sempre restituire una lista di NewsItem.
        """
        pass
