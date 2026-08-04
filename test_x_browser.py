from playwright.sync_api import sync_playwright


ACCOUNT = "FabrizioRomano"


def main():

    url = f"https://x.com/{ACCOUNT}"

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        print(f"Apro: {url}")

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(5000)

        tweets = page.locator(
            'article'
        )

        count = tweets.count()

        print(
            f"Tweet trovati: {count}"
        )

        for i in range(
            min(count, 5)
        ):

            try:

                text = tweets.nth(i).inner_text()

                print("\n--- TWEET ---")
                print(text[:500])

            except Exception as e:

                print(
                    "Errore:",
                    e
                )

        browser.close()


if __name__ == "__main__":
    main()
