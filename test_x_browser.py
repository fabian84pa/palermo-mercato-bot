from playwright.sync_api import sync_playwright


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
            print(f"ACCOUNT: @{account}")
            print("====================")

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(5000)

            tweets = page.locator(
                "article"
            )

            count = tweets.count()

            print(
                f"Tweet trovati: {count}"
            )

            for i in range(
                min(count, 3)
            ):

                text = tweets.nth(i).inner_text()

                print("\n--- TWEET ---")
                print(text[:400])

        browser.close()


if __name__ == "__main__":
    main()
