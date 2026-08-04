from core.engine import Engine
from core.classifier import classify_news
from core.priority import get_priority
from core.quality import get_quality_score

from providers.di_marzio_provider import DiMarzioProvider
from providers.tmw_provider import TMWProvider
from providers.palermo_fc_provider import PalermoFCProvider

from telegram_sender import send_message

from database import (
    load_seen_items,
    save_seen_items,
    is_seen,
    mark_as_seen,
)


MIN_QUALITY_SCORE = 30


def main():

    providers = [
        DiMarzioProvider(),
        TMWProvider(),
        PalermoFCProvider(),
    ]

    seen_items = load_seen_items()

    engine = Engine(providers)
    news = engine.fetch_all()

    print(f"Notizie trovate: {len(news)}")

    # Debug qualità di tutte le notizie trovate
    for item in news:
        score = get_quality_score(
            item.title,
            item.source
        )

        print(
            f"Qualità {score} | {item.source} | {item.title}"
        )

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

    quality_news = []

    for item in new_news:

        score = get_quality_score(
            item.title,
            item.source
        )

        print(
            f"Filtro qualità {score}: {item.title}"
        )

        if score >= MIN_QUALITY_SCORE:
            quality_news.append(item)

        else:
            mark_as_seen(
                item.id,
                seen_items
            )

    print(
        f"Notizie valide dopo filtro qualità: {len(quality_news)}"
    )

    if not quality_news:
        save_seen_items(seen_items)

        send_message(
            "ℹ️ <b>Palermo Mercato Bot</b>\n\n"
            "Nessuna notizia rilevante."
        )

        return

    quality_news.sort(
        key=lambda item: get_priority(
            item.title,
            item.source
        )
    )

    for item in quality_news[:3]:

        category = classify_news(
            item.title,
            item.source
        )

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
            f"{category}\n\n"
            f"📰 <b>{item.title}</b>\n\n"
            f"{summary_text}"
            f"📰 Fonte: <b>{item.source}</b>\n\n"
            f'🔗 <a href="{item.link}">Leggi articolo</a>'
        )

        send_message(message)

        mark_as_seen(
            item.id,
            seen_items
        )

    save_seen_items(seen_items)


if __name__ == "__main__":
    main()
