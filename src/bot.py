from core.engine import Engine
from core.classifier import classify_news
from core.priority import get_priority
from core.quality import get_quality_score
from core.entity import format_player
from core.translator import Translator

from providers.di_marzio_provider import DiMarzioProvider
from providers.palermo_fc_provider import PalermoFCProvider
from providers.x_provider import XProvider

from telegram_sender import send_message, send_photo

from database import (
    load_seen_items,
    save_seen_items,
    is_seen,
    mark_as_seen,
)


MIN_QUALITY_SCORE = 30



def _has_meaningful_text(text: str) -> bool:
    """True se il testo contiene abbastanza caratteri alfanumerici da avere senso da solo."""
    import re
    cleaned = re.sub(r"https?://\S+", " ", text or "")
    alnum = re.findall(r"[A-Za-zÀ-ÿ0-9]", cleaned)
    return len(alnum) >= 4


def _is_official_x_item(item) -> bool:
    return (
        item.source == "X Calciomercato"
        and "x-Palermofficial-" in item.id
    )


def _summary_is_redundant(title: str, summary: str) -> bool:
    import re

    t = re.sub(r"\\s+", " ", (title or "").casefold()).strip()
    s = re.sub(r"\\s+", " ", (summary or "").casefold()).strip()

    if not t or not s:
        return True

    return t == s or t in s or s in t


def _is_palermo_official_post(item) -> bool:
    return _is_official_x_item(item)



def main():


    providers = [

        DiMarzioProvider(),

        PalermoFCProvider(),

        XProvider(),

    ]



    seen_items = load_seen_items()



    print(
        f"Database notizie caricate: {len(seen_items)}"
    )



    engine = Engine(
        providers
    )


    news = engine.fetch_all()



    print(
        f"Notizie trovate: {len(news)}"
    )



    translator = Translator()



    for item in news:


        if item.source == "X Calciomercato":


            item.title = translator.translate(
                item.title
            )


            item.summary = translator.translate(
                item.summary
            )



    new_news = []



    for item in news:


        if not is_seen(
            item.id,
            seen_items
        ):

            new_news.append(
                item
            )


        else:

            print(
                f"Duplicato ignorato: {item.title}"
            )



    print(
        f"Nuove notizie: {len(new_news)}"
    )



    if not new_news:

        return



    quality_news = []



    for item in new_news:

        if (
            _is_official_x_item(item)
            and not item.image_url
            and not _has_meaningful_text(item.title)
        ):
            print(f"Scartato post Palermo senza foto/testo utile: {item.title}")
            mark_as_seen(item.id, seen_items)
            continue

        score = get_quality_score(

            item.title,

            item.source

        )


        print(
            f"QUALITÀ: {item.title} | Score: {score}"
        )



        if score >= MIN_QUALITY_SCORE:


            quality_news.append(
                item
            )


        else:


            mark_as_seen(
                item.id,
                seen_items
            )



    print(
        f"Notizie valide dopo filtro qualità: {len(quality_news)}"
    )



    if not quality_news:


        save_seen_items(
            seen_items
        )

        return



    quality_news.sort(

        key=lambda item:

        get_priority(

            item.title,

            item.source

        ),

        reverse=True

    )



    for item in quality_news[:3]:


        category = classify_news(
            item.title,
            item.source
        )

        # @Palermofficial è una comunicazione societaria.
        # Partite e infortuni mantengono la loro categoria specifica;
        # gli altri post ufficiali restano UFFICIALE.
        if _is_palermo_official_post(item):
            official_text = item.title.casefold()

            injury_markers = (
                "infortunio", "infortunato", "infortunati",
                "indisponibile", "lesione", "injury", "injured",
            )
            match_markers = (
                "match day", "matchday", "partita", "formazione",
                "convocati", "convocato", "calcio d'inizio",
                "diretta streaming", "full time", "finisce",
                "risultato", "vince", "vittoria", "sconfitta",
                "pareggio", "finale", "amichevole",
            )

            if any(x in official_text for x in injury_markers):
                category = "🚑 INFORTUNI"
            elif any(x in official_text for x in match_markers):
                category = "⚽ PARTITA"
            else:
                category = "🟢 UFFICIALE"


        player = format_player(item.title)

        player_text = ""

        market_categories = (
            "🟢 UFFICIALE",
            "🟠 TRATTATIVA AVANZATA",
            "🟡 RUMOR",
        )

        if player and category in market_categories:
            names = [x.strip() for x in player.split(",") if x.strip()]
            if len(names) > 1:
                player_text = (
                    f"👥 <b>Giocatori:</b> {', '.join(names)}\\n\\n"
                )
            else:
                player_text = (
                    f"👤 <b>Giocatore:</b> {player}\\n\\n"
                )


        summary_text = ""

        if (
            item.summary
            and item.source != "X Calciomercato"
            and not _summary_is_redundant(item.title, item.summary)
        ):
            short_summary = item.summary[:220]

            if len(item.summary) > 220:
                short_summary += "..."

            summary_text = (
                f"📝 <i>{short_summary}</i>\\n\\n"
            )


        breaking_words = (

            "breaking",

            "here we go",

            "affare fatto",

            "ufficiale",

            "accordo",

            "done deal",

            "medical",

            "visite mediche",

        )



        title_lower = item.title.lower()



        is_market = category in market_categories

        if is_market and any(

            word in title_lower

            for word in breaking_words

        ):


            header = (

                "🚨 <b>ULTIM'ORA PALERMO</b>"

            )


        else:


            header = (

                "🟣 <b>PALERMO LIVE</b>"

            )



        message = (


            f"{header}\n\n"

            f"{category}\n\n"

            f"{player_text}"

            f"📰 <b>{item.title}</b>\n\n"

            f"{summary_text}"

            f"📰 Fonte: <b>{item.source}</b>\n\n"

            f'🔗 <a href="{item.link}">Leggi articolo</a>'


        )



        if item.image_url:

            sent = send_photo(
                item.image_url,
                message
            )

            if not sent:
                print("Invio foto fallito, fallback a messaggio testuale.")
                send_message(message)

        else:

            send_message(
                message
            )



        mark_as_seen(

            item.id,

            seen_items

        )



    save_seen_items(

        seen_items

    )



if __name__ == "__main__":

    main()
