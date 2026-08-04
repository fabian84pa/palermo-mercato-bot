from providers.di_marzio_provider import fetch_di_marzio_news
from telegram_sender import send_message


def main():
    print("Controllo delle notizie di Gianluca Di Marzio...")

    news = fetch_di_marzio_news(limit=10)

    print(f"Notizie sul Palermo trovate: {len(news)}")

    if not news:
        send_message(
            "ℹ️ <b>Palermo Mercato Bot</b>\n\n"
            "Il controllo di Gianluca Di Marzio è riuscito, "
            "ma al momento non sono state trovate nuove notizie sul Palermo."
        )
        return

    item = news[0]

    message = (
        "🚨 <b>PALERMO CALCIOMERCATO</b>\n\n"
        f"📰 <b>{item.title}</b>\n\n"
        f"👤 Fonte: {item.source}\n\n"
        f'🔗 <a href="{item.link}">Apri la notizia</a>'
    )

    send_message(message)


if __name__ == "__main__":
    main()
