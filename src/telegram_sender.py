import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


TELEGRAM_API_TIMEOUT = 30
MAX_CAPTION_LENGTH = 1024


def _telegram_request(
    method: str,
    payload: dict,
) -> bool:
    """
    Esegue una richiesta alle Telegram Bot API.

    Restituisce True SOLO se Telegram risponde con:
        {"ok": true, ...}
    """

    if not TELEGRAM_BOT_TOKEN:
        print(
            "Errore: TELEGRAM_BOT_TOKEN non configurato."
        )
        return False

    if not TELEGRAM_CHAT_ID:
        print(
            "Errore: TELEGRAM_CHAT_ID non configurato."
        )
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/{method}"
    )

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=TELEGRAM_API_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("ok") is True:
            return True

        print(
            "Telegram ha restituito "
            f"ok=false: {data}"
        )

        return False

    except requests.RequestException as exc:

        print(
            f"Errore connessione Telegram: {exc}"
        )

        return False

    except ValueError as exc:

        print(
            f"Risposta Telegram non valida: {exc}"
        )

        return False

    except Exception as exc:

        print(
            f"Errore Telegram: {exc}"
        )

        return False


def send_message(
    message: str,
) -> bool:
    """
    Invia un messaggio Telegram.

    Restituisce True SOLO se l'API Telegram conferma
    esplicitamente l'avvenuto invio.
    """

    if not message:
        print(
            "Errore Telegram: messaggio vuoto."
        )
        return False

    # Telegram supporta messaggi fino a 4096 caratteri.
    if len(message) > 4096:

        print(
            "Messaggio troppo lungo: "
            "verrà troncato a 4096 caratteri."
        )

        message = message[:4096]

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    return _telegram_request(
        "sendMessage",
        payload,
    )


def send_photo(
    photo_url: str,
    caption: str,
) -> bool:
    """
    Invia una foto Telegram con caption HTML.

    Telegram limita la caption delle foto a 1024 caratteri.
    """

    if not photo_url:
        print(
            "Errore Telegram: photo_url vuoto."
        )
        return False

    if not caption:
        print(
            "Errore Telegram: caption vuota."
        )
        return False

    if len(caption) > MAX_CAPTION_LENGTH:

        print(
            "Caption foto troppo lunga: "
            "verrà troncata a 1024 caratteri."
        )

        caption = caption[
            :MAX_CAPTION_LENGTH
        ]

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
    }

    return _telegram_request(
        "sendPhoto",
        payload,
    )
