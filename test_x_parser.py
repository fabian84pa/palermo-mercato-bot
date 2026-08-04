import json
from datetime import datetime
from pathlib import Path


KEYWORDS_FILE = Path(
    "data/palermo_keywords.json"
)


def load_keywords():

    with open(
        KEYWORDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return tuple(
        data.get("keywords", [])
    )


def clean_tweet(text: str) -> str:

    lines = text.splitlines()

    cleaned = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if line.lower() == "pinned":
            continue

        if line.startswith("@"):
            continue

        cleaned.append(line)


    return " ".join(cleaned)



def is_palermo_news(text: str) -> bool:

    keywords = load_keywords()

    normalized = text.casefold()

    return any(
        keyword.casefold() in normalized
        for keyword in keywords
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

        "published":
            datetime.now().isoformat(),

        "summary": text

    }



if __name__ == "__main__":


    test = """
    Fabrizio Romano

    Palermo are in talks for a new signing.
    """


    cleaned = clean_tweet(
        test
    )


    print(
        "TESTO:"
    )

    print(
        cleaned
    )


    print(
        "\nPALERMO:"
    )

    print(
        is_palermo_news(
            cleaned
        )
    )


    print(
        "\nNEWS ITEM:"
    )

    print(
        create_news_item(
            "Fabrizio Romano",
            cleaned,
            "https://x.com/test"
        )
    )
