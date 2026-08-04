from core.engine import Engine
from core.classifier import classify_news
from core.priority import get_priority
from core.quality import get_quality_score
from core.entity import format_player

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

    new_news = [
        item for item in news
        if not is_seen(item.id, seen_items)
    ]

    print(f"Nuove notizie: {len(new_news)}")

    if not new_news:
        return

    quality_news = []

    for item in new_news:

        score = get_quality_score(
            item.title,
            item.source
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

        player = format_player(
            item.title
        )

        player_text = ""

        if player:
            player_text = (
                f"{player}\n\n"
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
            f"{player_text}"
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
