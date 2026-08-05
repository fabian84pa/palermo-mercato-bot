from core.engine import Engine
from core.classifier import classify_news
from core.priority import get_priority
from core.quality import get_quality_score
from core.entity import format_player
from core.translator import Translator

from providers.di_marzio_provider import DiMarzioProvider
from providers.palermo_fc_provider import PalermoFCProvider
from providers.x_provider import XProvider

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



        player = format_player(

            item.title

        )



        player_text = ""



        if player:

            player_text = (

                f"👤 <b>Giocatore:</b> {player}\n\n"

            )



        summary_text = ""



        if item.summary:


            short_summary = item.summary[:220]


            if len(item.summary) > 220:

                short_summary += "..."



            summary_text = (

                f"📝 <i>{short_summary}</i>\n\n"

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



        if any(

            word in title_lower

            for word in breaking_words

        ):


            header = (

                "🚨 <b>ULTIM'ORA PALERMO</b>"

            )


        else:


            header = (

                "🟣 <b>PALERMO CALCIOMERCATO</b>"

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
