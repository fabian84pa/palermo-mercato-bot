from deep_translator import GoogleTranslator


class Translator:

    FOOTBALL_TERMS = {

        "here we go": "affare fatto",
        "agreement": "accordo",
        "deal": "affare",
        "done deal": "affare concluso",
        "medical tests": "visite mediche",
        "medical": "visite mediche",
        "signing": "acquisto",
        "signed": "firmato",
        "contract signed": "contratto firmato",
        "contract until": "contratto fino al",
        "talks": "trattative",
        "in talks": "in trattativa",
        "opened talks": "ha aperto la trattativa",
        "close to": "vicino a",
        "close": "vicino",
        "bid": "offerta",
        "offer": "offerta",
        "proposal": "proposta",
        "player": "giocatore",
        "club": "club",
        "fee": "cifra",
        "loan": "prestito",
        "permanent deal": "trasferimento definitivo",
        "free agent": "svincolato",
        "exclusive": "esclusiva",
        "breaking": "ultim'ora"
    }


    def __init__(self):

        self.translator = GoogleTranslator(
            source="auto",
            target="it"
        )


    def apply_dictionary(
        self,
        text: str
    ) -> str:

        result = text

        for eng, ita in self.FOOTBALL_TERMS.items():

            result = result.replace(
                eng,
                ita
            )

            result = result.replace(
                eng.title(),
                ita
            )

            result = result.replace(
                eng.upper(),
                ita.upper()
            )

        return result


    def translate(
        self,
        text: str
    ) -> str:


        if not text:
            return ""


        try:

            translated = self.translator.translate(
                text
            )


        except Exception:

            # fallback:
            # se Google fallisce mantiene il testo

            translated = text



        translated = self.apply_dictionary(
            translated
        )


        return translated.strip()



if __name__ == "__main__":


    translator = Translator()


    tests = [

        "Palermo are in talks with a new signing.",

        "Here we go! Agreement completed for the Italian club.",

        "Exclusive: Palermo have opened talks for the player.",

        "Medical tests completed. Contract signed until 2030."

    ]


    for text in tests:

        print("\n====================")

        print(
            "INGLESE:"
        )

        print(
            text
        )

        print(
            "\nITALIANO:"
        )

        print(
            translator.translate(text)
        )
