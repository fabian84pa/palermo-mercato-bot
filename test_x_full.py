from playwright.sync_api import sync_playwright

from test_x_parser import (
    clean_tweet,
    is_palermo_news,
    create_news_item,
)


ACCOUNTS = [
    "FabrizioRomano",
    "NicoSchira",
    "DiMarzio",
    "MatteMoretto",
]


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()


        for account in ACCOUNTS:

            url = f"https://x.com/{account}"

            print("\n====================")
            print(f"CONTROLLO: @{account}")
            print("====================")


            try:

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                page.wait_for_timeout(
                    5000
                )


                tweets = page.locator(
                    "article"
                )

                count = tweets.count()

                print(
                    f"Tweet trovati: {count}"
                )


                for i in range(
                    min(count, 5)
                ):

                    raw_text = tweets.nth(i).inner_text()


                    text = clean_tweet(
                        raw_text
                    )


                    if not text:
                        continue


                    if is_palermo_news(
                        text
                    ):

                        news = create_news_item(
                            account,
                            text,
                            url
                        )


                        print(
                            "\n🚨 NOTIZIA PALERMO"
                        )

                        print(
                            news
                        )


                    else:

                        print(
                            "\nIgnorata:"
                        )

                        print(
                            text[:120]
                        )


            except Exception as e:

                print(
                    "Errore:",
                    e
                )


        browser.close()


if __name__ == "__main__":
    main()
