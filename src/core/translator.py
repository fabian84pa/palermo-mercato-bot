from deep_translator import GoogleTranslator


class Translator:

    def __init__(self):

        self.translator = GoogleTranslator(
            source="auto",
            target="it"
        )


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

            return translated.strip()


        except Exception:

            return text



if __name__ == "__main__":

    translator = Translator()


    test = (
        "Palermo are in talks "
        "with a new signing."
    )


    print(
        "Originale:"
    )

    print(
        test
    )


    print(
        "\nTradotto:"
    )

    print(
        translator.translate(
            test
        )
    )
