import sys

sys.path.append(
    "src"
)

from core.translator import Translator


def main():

    translator = Translator()

    tests = [

        "Palermo are in talks with a new signing.",

        "Here we go! Agreement completed for the Italian club.",

        "Exclusive: Palermo have opened talks for the player."

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


if __name__ == "__main__":
    main()
