from datetime import datetime


KEYWORDS = (
    "palermo",
    "palermo fc",
    "rosanero",
    "rosaneri",
    "inzaghi",
)


def clean_tweet(text: str) -> str:
    """
    Pulisce il testo del tweet.
    """

    lines = text.splitlines()

    cleaned = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if line.startswith("@"):
            continue

        if line.lower() == "pinned":
            continue

        cleaned.append(line)

    return " ".join(cleaned)


def is_palermo_news(text: str) -> bool:
    """
    Controlla se il tweet riguarda Palermo.
    """

    normalized = text.casefold()

    return any(
        keyword in normalized
        for keyword in KEYWORDS
    )


def create_news_item(
    author: str,
    text: str,
    link: str
):

    return {
        "title": text[:120],
        "source": f"X - {author}",
        "link": link,
        "published": datetime.now().isoformat(),
        "summary": text,
    }


if __name__ == "__main__":

    test_tweet = """
    Fabrizio Romano
    @FabrizioRomano

    Palermo are pushing for Gabriel Strefezza.
    Talks ongoing.
    """

    cleaned = clean_tweet(
        test_tweet
    )

    print(
        "TESTO PULITO:"
    )

    print(
        cleaned
    )


    print(
        "\nPalermo news:"
    )

    print(
        is_palermo_news(
            cleaned
        )
    )


    item = create_news_item(
        "Fabrizio Romano",
        cleaned,
        "https://x.com/test"
    )


    print(
        "\nNEWS ITEM:"
    )

    print(
        item
    )
