import requests


ACCOUNTS = [
    "FabrizioRomano",
    "NicoSchira",
    "DiMarzio",
    "MatteMoretto",
]


SOURCES = [
    "https://nitter.nerdvpn.de/",
    "https://nitter.privacydev.net/",
]


def test_source(base_url, account):

    url = f"{base_url}{account}"

    print(
        f"\nTest: {url}"
    )

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0"
                )
            }
        )

        print(
            "Status:",
            response.status_code
        )

        if response.status_code == 200:

            text = response.text[:200]

            print(
                "OK:",
                text.replace("\n", " ")
            )

            return True

    except Exception as e:

        print(
            "Errore:",
            e
        )

    return False


for source in SOURCES:

    for account in ACCOUNTS:

        test_source(
            source,
            account
        )
