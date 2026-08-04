from core.engine import Engine
from providers.di_marzio_provider import DiMarzioProvider
from telegram_sender import send_message


def main():
    providers = [
        DiMarzioProvider(),
    ]

    engine = Engine(providers)
    news = engine.fetch_all()

    print(f"Notizie trovate: {len(news)}")

    if not news:
        send_message(
            "ℹ️ <b>Palermo Mercato Bot</b>\n\n"
            "Nessuna nuova notizia trovata da Gianluca Di Marzio."
        )
        return

    for item in news[:5]:
        message = (
            "🚨 <b>PALERMO CALCIOMERCATO</b>\n\n"
            f"📰 <b>{item.title}</b>\n\n"
            f"👤 Fonte: {item.source}\n\n"
            f'🔗 <a href="{item.link}">Apri la notizia</a>'
        )

        send_message(message)


if __name__ == "__main__":
    main()
