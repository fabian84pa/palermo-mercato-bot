import json
import re
from pathlib import Path


DATABASE_FILE = Path("data/seen.json")


# ==========================================================
# LOAD
# ==========================================================

def load_seen_items() -> set[str]:
    """
    Carica gli identificativi delle notizie già inviate.

    Gli ID vengono mantenuti come stringhe.
    I vecchi ID X generati con hash() vengono rimossi perché
    non sono stabili tra diverse esecuzioni del programma.
    """

    if not DATABASE_FILE.exists():
        return set()

    try:

        content = DATABASE_FILE.read_text(
            encoding="utf-8"
        )

        data = json.loads(
            content
        )

        if not isinstance(
            data,
            list,
        ):
            return set()

        items = {
            str(item).strip()
            for item in data
            if str(item).strip()
        }

        cleaned_items = set()

        for item in items:

            # --------------------------------------------------
            # Vecchi ID X creati con hash() di Python.
            #
            # Esempi:
            # x-FabrizioRomano-5744720463395066101
            # x-DiMarzio--4539733307024404931
            #
            # NON devono essere mantenuti perché gli ID nuovi
            # sono generati in modo stabile.
            # --------------------------------------------------

            if re.match(
                r"^x-(FabrizioRomano|MatteMoretto|DiMarzio|NicoSchira)-?-?\d+$",
                item,
            ):
                print(
                    f"Vecchio ID X rimosso: {item}"
                )
                continue

            cleaned_items.add(
                item
            )

        return cleaned_items

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:

        print(
            f"Errore caricamento database: {exc}"
        )

        return set()


# ==========================================================
# SAVE
# ==========================================================

def save_seen_items(
    items: set[str],
) -> None:
    """
    Salva gli identificativi delle notizie già inviate.
    """

    DATABASE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Manteniamo soltanto stringhe non vuote.
    cleaned_items = {
        str(item).strip()
        for item in items
        if str(item).strip()
    }

    DATABASE_FILE.write_text(
        json.dumps(
            sorted(
                cleaned_items
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ==========================================================
# CHECK
# ==========================================================

def is_seen(
    item_id: str,
    seen_items: set[str],
) -> bool:
    """
    Controlla se una notizia è già stata inviata.
    """

    if not item_id:
        return False

    return str(
        item_id
    ).strip() in seen_items


# ==========================================================
# MARK
# ==========================================================

def mark_as_seen(
    item_id: str,
    seen_items: set[str],
) -> None:
    """
    Segna una notizia come già inviata.

    IMPORTANTE:
    questa funzione NON salva direttamente il file.
    Il chiamante deve eseguirla solo dopo un invio Telegram
    riuscito e poi chiamare save_seen_items().
    """

    if not item_id:
        return

    item_id = str(
        item_id
    ).strip()

    if not item_id:
        return

    seen_items.add(
        item_id
    )
