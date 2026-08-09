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




def _clean_x_display_text(text: str) -> str:
    import re
    if not text:
        return text
    kept = []
    for line in text.splitlines():
        s = line.strip()
        if re.fullmatch(r"\d+\s*[mh]", s, flags=re.I):
            continue
        if re.fullmatch(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}", s, flags=re.I):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _deal_tokens(item):
    import re
    text = f"{item.title} {item.summary or ''}".casefold()
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"[^a-zà-ÿ0-9]+", " ", text)
    stop = {"palermo","calcio","calciomercato","mercato","della","delle","degli",
            "dell","sono","questo","questa","anche","with","from","that","this",
            "the","and","for","per","con","del","dei","gli","una","uno"}
    return {w for w in text.split() if len(w) >= 4 and w not in stop}


def _same_deal(a, b):
    ta, tb = _deal_tokens(a), _deal_tokens(b)
    if not ta or not tb:
        return False
    common = ta & tb
    overlap = len(common) / max(1, min(len(ta), len(tb)))
    return len(common) >= 2 and overlap >= 0.35


def _source_rank(item):
    source = (item.source or "").casefold()
    if source == "x calciomercato":
        return 0
    if "palermo" in source:
        return 3
    if "di marzio" in source:
        return 2
    return 1


def _deduplicate_same_deals(items):
    selected = []
    for item in items:
        match = next((i for i, old in enumerate(selected) if _same_deal(item, old)), None)
        if match is None:
            selected.append(item)
        elif _source_rank(item) > _source_rank(selected[match]):
            print(f"Notizia simile sostituita: {selected[match].title} -> {item.title}")
            selected[match] = item
        else:
            print(f"Notizia simile ignorata: {item.title}")
    return selected


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

            item.title = _clean_x_display_text(item.title)
            item.summary = _clean_x_display_text(item.summary)



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



    quality_news = _deduplicate_same_deals(quality_news)

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
