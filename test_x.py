from twikit import Client
import asyncio


ACCOUNTS = [
    "FabrizioRomano",
    "NicoSchira",
    "DiMarzio",
    "MatteMoretto",
]


async def main():

    client = Client(
        "en-US"
    )

    for account in ACCOUNTS:

        print("\n====================")
        print(f"Test account: @{account}")
        print("====================")

        try:

            user = await client.get_user_by_screen_name(
                account
            )

            print(
                f"ID trovato: {user.id}"
            )

            tweets = await client.get_user_tweets(
                user.id,
                "Tweets",
                count=3
            )

            for tweet in tweets:

                print(
                    tweet.created_at,
                    "|",
                    tweet.text[:150]
                )

        except Exception as e:

            print(
                "Errore:",
                e
            )


asyncio.run(main())
