from telegram_sender import send_message
from sources import fetch_google_news


def main():
    print("Palermo Mercato Bot avviato")

    news = fetch_google_news(limit=1)

    if not news:
        send_message("❌ Nessuna notizia trovata.")
        return

    item = news[0]

    message = (
        "📰 <b>Prima notizia trovata</b>\n\n"
        f"<b>{item.title}</b>\n\n"
        f"📰 Fonte: {item.source}\n"
        f"📅 Data: {item.published}\n\n"
        f'🔗 <a href="{item.link}">Apri la notizia</a>'
    )

    send_message(message)


if __name__ == "__main__":
    main()
