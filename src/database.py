import json
import re
from pathlib import Path


DATABASE_FILE = Path("data/seen.json")


def load_seen_items() -> set[str]:
    """
    Carica gli identificativi delle notizie già inviate.
    """

    if not DATABASE_FILE.exists():
        return set()


    try:

        content = DATABASE_FILE.read_text(
            encoding="utf-8"
        )

        data = json.loads(content)


        if not isinstance(data, list):
            return set()


        items = set(
            str(item)
            for item in data
        )


        # Rimuove vecchi ID X generati con hash()
        # esempio:
        # x-FabrizioRomano-5744720463395066101
        # x-DiMarzio--4539733307024404931

        cleaned_items = set()


        for item in items:

            if re.match(
                r"^x-(FabrizioRomano|MatteMoretto|DiMarzio|NicoSchira)-?-?\d+$",
                item
            ):
                continue


            cleaned_items.add(item)


        return cleaned_items



    except (
        OSError,
        json.JSONDecodeError
    ):

        return set()



def save_seen_items(items: set[str]) -> None:
    """
    Salva gli identificativi delle notizie già inviate.
    """

    DATABASE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    DATABASE_FILE.write_text(

        json.dumps(
            sorted(items),
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )



def is_seen(
    item_id: str,
    seen_items: set[str]
) -> bool:
    """
    Controlla se una notizia è già stata inviata.
    """

    return item_id in seen_items



def mark_as_seen(
    item_id: str,
    seen_items: set[str]
) -> None:
    """
    Segna una notizia come già inviata.
    """

    seen_items.add(item_id)
