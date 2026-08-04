import snscrape.modules.twitter as sntwitter


ACCOUNTS = [
    "FabrizioRomano",
    "NicoSchira",
    "DiMarzio",
    "MatteMoretto",
]


for account in ACCOUNTS:

    print("\n====================")
    print(f"Test account: @{account}")
    print("====================")

    try:

        scraper = sntwitter.TwitterUserScraper(
            account
        )

        count = 0

        for tweet in scraper.get_items():

            print(
                tweet.date,
                "|",
                tweet.rawContent[:150]
            )

            count += 1

            if count >= 3:
                break

        if count == 0:
            print("Nessun tweet trovato")

    except Exception as e:

        print(
            "Errore:",
            e
        )
