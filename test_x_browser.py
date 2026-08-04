from playwright.sync_api import sync_playwright


ACCOUNT = "FabrizioRomano"


def main():

    url = f"https://x.com/{ACCOUNT}"

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1280,
                "height": 2000
            }
        )

        print(
            f"Apro: {url}"
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(
            5000
        )

        text = page.locator(
            "body"
        ).inner_text()

        print(
            text[:3000]
        )

        browser.close()


if __name__ == "__main__":
    main()
