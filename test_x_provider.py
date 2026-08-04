import sys

sys.path.append(
    "src"
)

from providers.x_provider import XProvider


def main():

    print(
        "Avvio test XProvider"
    )

    provider = XProvider()

    news = provider.fetch()

    print(
        f"\nNotizie trovate: {len(news)}"
    )

    for item in news:

        print(
            "\n===================="
        )

        print(
            "Titolo:",
            item.title
        )

        print(
            "Fonte:",
            item.source
        )

        print(
            "Link:",
            item.link
        )

        print(
            "Summary:",
            item.summary
        )


if __name__ == "__main__":
    main()
