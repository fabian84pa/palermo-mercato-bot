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
MAX_MESSAGES_PER_RUN = 3


def _has_meaningful_text(text: str) -> bool:
    """True se il testo contiene abbastanza caratteri alfanumerici."""
    import re

    cleaned = re.sub(
        r"https?://\S+",
        " ",
        text or "",
    )

    alnum = re.findall(
        r"[A-Za-zÀ-ÿ0-9]",
        cleaned,
    )

    return len(alnum) >= 4


def _is_official_x_item(item) -> bool:
    return (
        item.source == "X Calciomercato"
        and "x-Palermofficial-" in item.id
    )


def _clean_display_text(
    text: str,
    *,
    single_line: bool = False,
) -> str:
    """
    Pulisce testo proveniente da X/HTML prima della
    pubblicazione Telegram.
    """

    import re

    if not text:
        return ""

    # Caratteri letterali "\n" restituiti da alcuni provider.
    text = text.replace(
        "\\r\\n",
        "\n",
    )

    text = text.replace(
        "\\n",
        "\n",
    )

    text = text.replace(
        "\\r",
        "\n",
    )

    # Veri caratteri newline.
    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    if single_line:

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

    else:

        text = "\n".join(
            line.strip()
            for line in text.split("\n")
            if line.strip()
        )

    return text.strip()


def _summary_is_redundant(
    title: str,
    summary: str,
) -> bool:

    import re

    t = re.sub(
        r"\s+",
        " ",
        _clean_display_text(
            title,
            single_line=True,
        ).casefold(),
    ).strip()

    s = re.sub(
        r"\s+",
        " ",
        _clean_display_text(
            summary,
            single_line=True,
        ).casefold(),
    ).strip()

    if not t or not s:
        return True

    if t == s:
        return True

    if t in s:
        return True

    if s in t:
        return True

    # Se il summary è quasi completamente composto dalle
    # stesse parole del titolo, non lo mostriamo due volte.
    title_words = set(t.split())
    summary_words = set(s.split())

    if (
        len(title_words) >= 5
        and len(summary_words) >= 5
    ):

        overlap = (
            len(title_words & summary_words)
            / min(
                len(title_words),
                len(summary_words),
            )
        )

        if overlap >= 0.85:
            return True

    return False


def _deal_tokens(item):

    """
    Tokenizza titolo + summary per individuare
    la stessa trattativa ripetuta.
    """

    import re

    text = _clean_display_text(
        f"{item.title} {item.summary or ''}",
        single_line=True,
    ).casefold()

    text = re.sub(
        r"@\w+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-zà-ÿ0-9]+",
        " ",
        text,
    )

    stop = {
        "palermo",
        "calcio",
        "calciomercato",
        "mercato",
        "della",
        "delle",
        "degli",
        "dell",
        "sono",
        "questo",
        "questa",
        "anche",
        "with",
        "from",
        "that",
        "this",
        "the",
        "and",
        "for",
        "per",
        "con",
        "del",
        "dei",
        "gli",
        "una",
        "uno",
        "tra",
        "alla",
        "il",
        "la",
        "le",
        "un",
        "di",
        "a",
        "in",
        "si",
        "ha",
        "dal",
        "dalla",
        "che",
        "come",
        "sul",
        "sulla",
        "sullo",
        "nel",
        "nella",
        "nelle",
        "con",
        "anche",
    }

    return {
        word
        for word in text.split()
        if len(word) >= 4
        and word not in stop
    }


def _same_deal(a, b):

    """
    Evita due post sullo stesso affare senza fondere
    automaticamente notizie diverse.
    """

    import re

    ta = _deal_tokens(a)
    tb = _deal_tokens(b)

    if not ta or not tb:
        return False

    title_a = set(
        re.findall(
            r"[a-zà-ÿ0-9]+",
            _clean_display_text(
                a.title,
                single_line=True,
            ).casefold(),
        )
    )

    title_b = set(
        re.findall(
            r"[a-zà-ÿ0-9]+",
            _clean_display_text(
                b.title,
                single_line=True,
            ).casefold(),
        )
    )

    common_title = title_a & title_b

    generic = {
        "palermo",
        "trattativa",
        "mercato",
        "calcio",
        "calciomercato",
        "accordo",
        "offerta",
        "interesse",
        "profilo",
        "profili",
        "nuovo",
        "nuova",
        "portiere",
        "giocatore",
        "giocatori",
        "club",
        "serie",
    }

    specific = common_title - generic

    # Se condividono almeno due token specifici nel titolo,
    # è molto probabile che parlino dello stesso giocatore/affare.
    if (
        specific
        and len(
            common_title
            - {
                "il",
                "la",
                "di",
                "per",
                "al",
                "del",
                "si",
                "a",
                "un",
            }
        ) >= 2
    ):
        return True

    common = ta & tb

    overlap = (
        len(common)
        / max(
            1,
            min(
                len(ta),
                len(tb),
            ),
        )
    )

    return (
        len(common) >= 4
        and overlap >= 0.60
    )


def _source_rank(item):

    source = (
        item.source or ""
    ).casefold()

    if source == "x calciomercato":
        return 0

    if "palermo" in source:
        return 3

    if "di marzio" in source:
        return 2

    if (
        "schira" in source
        or "moretto" in source
        or "romano" in source
    ):
        return 2

    return 1


def _deduplicate_same_deals(items):

    """
    Tiene una sola notizia per lo stesso affare,
    privilegiando la fonte migliore.
    """

    selected = []

    for item in items:

        match = next(
            (
                index
                for index, old in enumerate(selected)
                if _same_deal(
                    item,
                    old,
                )
            ),
            None,
        )

        if match is None:

            selected.append(
                item
            )

        elif (
            _source_rank(item)
            > _source_rank(
                selected[match]
            )
        ):

            print(
                "Notizia simile sostituita: "
                f"{selected[match].title} -> "
                f"{item.title}"
            )

            selected[match] = item

        else:

            print(
                "Notizia simile ignorata: "
                f"{item.title}"
            )

    return selected


def _is_palermo_official_post(item):
    return _is_official_x_item(item)


def _is_invalid_technical_post(item) -> bool:

    """
    Blocca risposte tecniche finite accidentalmente
    nel flusso delle notizie.
    """

    text = _clean_display_text(
        f"{item.title} {item.summary or ''}",
        single_line=True,
    ).casefold()

    invalid_markers = (
        "error 500",
        "server error",
        "internal server error",
        "that's an error",
        "something went wrong",
        "please try again later",
        "bad gateway",
        "service unavailable",
        "gateway timeout",
        "error 502",
        "error 503",
        "error 504",
    )

    return any(
        marker in text
        for marker in invalid_markers
    )


def _escape_html(text: str) -> str:

    """
    Escape minimo per Telegram HTML.
    """

    import html

    return html.escape(
        text or "",
        quote=False,
    )


def main():

    providers = [
        DiMarzioProvider(),
        PalermoFCProvider(),
        XProvider(),
    ]

    seen_items = load_seen_items()

    print(
        f"Database notizie caricate: "
        f"{len(seen_items)}"
    )

    engine = Engine(
        providers
    )

    news = engine.fetch_all()

    print(
        f"Notizie trovate: "
        f"{len(news)}"
    )

    translator = Translator()

    for item in news:

        # ------------------------------------------------------
        # BLOCCO ERRORI TECNICI
        # ------------------------------------------------------

        if _is_invalid_technical_post(
            item
        ):

            print(
                "POST TECNICO SCARTATO: "
                f"{item.title}"
            )

            # NON viene marcato come visto:
            # vogliamo poterlo rivalutare se il provider
            # restituisce successivamente il contenuto reale.
            continue

        # ------------------------------------------------------
        # TRADUZIONE X
        # ------------------------------------------------------

        if (
            item.source
            == "X Calciomercato"
        ):

            item.title = translator.translate(
                item.title
            )

            item.summary = translator.translate(
                item.summary
            )

        # ------------------------------------------------------
        # PULIZIA TESTO
        # ------------------------------------------------------

        item.title = _clean_display_text(
            item.title,
            single_line=True,
        )

        item.summary = _clean_display_text(
            item.summary
        )

    # ----------------------------------------------------------
    # NUOVE NOTIZIE
    # ----------------------------------------------------------

    new_news = []

    for item in news:

        if _is_invalid_technical_post(
            item
        ):
            continue

        if not item.id:
            print(
                "Notizia senza ID scartata: "
                f"{item.title}"
            )
            continue

        if not is_seen(
            item.id,
            seen_items,
        ):

            new_news.append(
                item
            )

        else:

            print(
                f"Duplicato ignorato: "
                f"{item.title}"
            )

    print(
        f"Nuove notizie: "
        f"{len(new_news)}"
    )

    if not new_news:
        return

    # ----------------------------------------------------------
    # FILTRO QUALITÀ
    # ----------------------------------------------------------

    quality_news = []

    for item in new_news:

        if (
            _is_official_x_item(item)
            and not item.image_url
            and not _has_meaningful_text(
                item.title
            )
        ):

            print(
                "Scartato post Palermo "
                "senza foto/testo utile: "
                f"{item.title}"
            )

            # NON marcare seen.
            # Potrebbe essere recuperato correttamente
            # a un'esecuzione successiva.
            continue

        score = get_quality_score(
            item.title,
            item.source,
        )

        print(
            f"QUALITÀ: {item.title} | "
            f"Score: {score}"
        )

        if score >= MIN_QUALITY_SCORE:

            quality_news.append(
                item
            )

        else:

            # IMPORTANTE:
            # non marchiamo la notizia come vista.
            # Se il filtro viene migliorato, potrà essere
            # rivalutata nelle esecuzioni successive.

            print(
                "Notizia sotto soglia, "
                "NON marcata come vista: "
                f"{item.title}"
            )

    print(
        "Notizie valide dopo filtro qualità: "
        f"{len(quality_news)}"
    )

    if not quality_news:
        save_seen_items(
            seen_items
        )
        return

    # ----------------------------------------------------------
    # DEDUPLICA TRATTATIVE
    # ----------------------------------------------------------

    quality_news = _deduplicate_same_deals(
        quality_news
    )

    # ----------------------------------------------------------
    # PRIORITÀ
    # ----------------------------------------------------------

    quality_news.sort(
        key=lambda item:
        get_priority(
            item.title,
            item.source,
        ),
        reverse=True,
    )

    # ----------------------------------------------------------
    # INVIO MASSIMO 3 NOTIZIE
    # ----------------------------------------------------------

    for item in quality_news[
        :MAX_MESSAGES_PER_RUN
    ]:

        category = classify_news(
            item.title,
            item.source,
        )

        # ------------------------------------------------------
        # PALERMO OFFICIAL
        # ------------------------------------------------------

        if _is_palermo_official_post(
            item
        ):

            official_text = (
                item.title or ""
            ).casefold()

            injury_markers = (
                "infortunio",
                "infortunato",
                "infortunati",
                "indisponibile",
                "lesione",
                "injury",
                "injured",
            )

            match_markers = (
                "match day",
                "matchday",
                "partita",
                "formazione",
                "convocati",
                "convocato",
                "calcio d'inizio",
                "kick off",
                "kick-off",
                "half time",
                "half-time",
                "intervallo",
                "sostituzione",
                "diretta streaming",
                "full time",
                "finisce",
                "risultato",
                "vince",
                "vittoria",
                "sconfitta",
                "pareggio",
                "finale",
                "amichevole",
            )

            if any(
                x in official_text
                for x in injury_markers
            ):

                category = (
                    "🚑 INFORTUNI"
                )

            elif any(
                x in official_text
                for x in match_markers
            ):

                category = (
                    "⚽ PARTITA"
                )

            else:

                category = (
                    "🟢 UFFICIALE"
                )

        # ------------------------------------------------------
        # TESTO FINALE
        # ------------------------------------------------------

        item.title = _clean_display_text(
            item.title,
            single_line=True,
        )

        item.summary = _clean_display_text(
            item.summary
        )

        player = format_player(
            item.title
        )

        player_text = ""

        market_categories = (
            "🟢 UFFICIALE",
            "🟠 TRATTATIVA AVANZATA",
            "🟡 RUMOR",
        )

        if (
            player
            and category in market_categories
        ):

            names = [
                name.strip()
                for name in player.split(",")
                if name.strip()
            ]

            if len(names) > 1:

                player_text = (
                    "👥 <b>Giocatori:</b> "
                    f"{_escape_html(', '.join(names))}"
                    "\n\n"
                )

            else:

                player_text = (
                    "👤 <b>Giocatore:</b> "
                    f"{_escape_html(player)}"
                    "\n\n"
                )

        # ------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------

        summary_text = ""

        if (
            item.summary
            and item.source
            != "X Calciomercato"
            and not _summary_is_redundant(
                item.title,
                item.summary,
            )
        ):

            short_summary = (
                item.summary[:220]
            )

            if len(item.summary) > 220:
                short_summary += "..."

            summary_text = (
                "📝 <i>"
                f"{_escape_html(short_summary)}"
                "</i>\n\n"
            )

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

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

        title_lower = (
            item.title.casefold()
        )

        is_market = (
            category in market_categories
        )

        if (
            is_market
            and any(
                word in title_lower
                for word in breaking_words
            )
        ):

            header = (
                "🚨 <b>ULTIM'ORA PALERMO</b>"
            )

        else:

            header = (
                "🟣 <b>PALERMO LIVE</b>"
            )

        # ------------------------------------------------------
        # LINK
        # ------------------------------------------------------

        safe_title = _escape_html(
            item.title
        )

        safe_source = _escape_html(
            item.source
        )

        safe_link = _escape_html(
            item.link
        )

        message = (
            f"{header}\n\n"
            f"{category}\n\n"
            f"{player_text}"
            f"📰 <b>{safe_title}</b>\n\n"
            f"{summary_text}"
            f"📰 Fonte: <b>{safe_source}</b>\n\n"
            f'<a href="{safe_link}">'
            "🔗 Leggi articolo"
            "</a>"
        )

        # ------------------------------------------------------
        # INVIO TELEGRAM
        # ------------------------------------------------------

        sent = False

        if item.image_url:

            sent = send_photo(
                item.image_url,
                message,
            )

            if not sent:

                print(
                    "Invio foto fallito, "
                    "fallback a messaggio testuale."
                )

                sent = send_message(
                    message
                )

        else:

            sent = send_message(
                message
            )

        # ------------------------------------------------------
        # DATABASE
        # ------------------------------------------------------

        if sent:

            mark_as_seen(
                item.id,
                seen_items,
            )

            print(
                f"INVIATA: "
                f"{item.title}"
            )

        else:

            print(
                "INVIO FALLITO - "
                "NON marcata come vista: "
                f"{item.title}"
            )

    save_seen_items(
        seen_items
    )


if __name__ == "__main__":
    main()
