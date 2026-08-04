from dataclasses import dataclass


@dataclass(slots=True)
class NewsItem:
    """
    Modello standard di una notizia.

    Tutti i provider (Di Marzio, TMW, Palermo FC, ecc.)
    dovranno restituire sempre un oggetto NewsItem.
    """

    id: str
    title: str
    link: str
    source: str
    published: str
    summary: str = ""
