import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_message(message: str) -> bool:
    """
    Invia un messaggio Telegram.
    Restituisce True se l'invio è andato a buon fine.
    """

    if not TELEGRAM_BOT_TOKEN:
        print("Errore: TELEGRAM_BOT_TOKEN non configurato.")
        return False

    if not TELEGRAM_CHAT_ID:
        print("Errore: TELEGRAM_CHAT_ID non configurato.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return True

    except Exception as e:
        print(f"Errore Telegram: {e}")
        return False
