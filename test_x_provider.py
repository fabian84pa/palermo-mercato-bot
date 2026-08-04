import sys

sys.path.append("src")

from providers.x_provider import XProvider


def main():

    provider = XProvider()

    test_tweets = [

        "🚨 BREAKING: Palermo are in talks for a new signing. Agreement close.",

        "Exclusive: Rosanero interested in a Serie B midfielder.",

        "Manchester United complete deal for player."

    ]


    for tweet in test_tweets:

        print("\n====================")
        print("TEST:")
        print(tweet)

        result = provider.is_relevant(tweet)

        print(
            "PASSA FILTRO:",
            result
        )


if __name__ == "__main__":
    main()
