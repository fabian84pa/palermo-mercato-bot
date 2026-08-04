from core.engine import Engine
from providers.di_marzio_provider import DiMarzioProvider
from telegram_sender import send_message

from database import (
    load_seen_items,
    save_seen_items,
    is_seen,
    mark_as_seen,
)


def main():
    providers = [
        DiMarzioProvider(),
    ]

    seen_items = load_seen_items()

    engine = Engine(providers)
    news = engine.fetch_all()

    print(f"Notizie trovate: {len(news)}")

    new_news = [
        item for item in news
        if not is_seen(item.id, seen_items)
    ]

    print(f"Nuove notizie: {len(new_news)}")

    if not new_news:
        send_message(
            "ℹ️ <b>Palermo Mercato Bot</b>\n\n"
            "Nessuna nuova notizia."
        )
        return

    for item in new_news[:5]:

        summary_text = ""

        if item.summary:
            short_summary = item.summary[:220]

            if len(item.summary) > 220:
                short_summary += "..."

            summary_text = (
                f"📝 <i>{short_summary}</i>\n\n"
            )

        message = (
            "🚨 <b>PALERMO CALCIOMERCATO</b>\n\n"
            f"📰 <b>{item.title}</b>\n\n"
            f"{summary_text}"
            f"👤 Fonte: {item.source}\n\n"
            f'🔗 <a href="{item.link}">Apri la notizia</a>'
        )

        send_message(message)

        mark_as_seen(item.id, seen_items)

    save_seen_items(seen_items)


if __name__ == "__main__":
    main()
