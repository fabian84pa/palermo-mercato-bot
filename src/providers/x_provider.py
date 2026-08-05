def generate_id(
    self,
    source,
    text
):

    """
    Genera un ID stabile per X.
    Ignora numeri e statistiche variabili.
    """

    import re


    clean = text.casefold()


    # elimina numeri, visualizzazioni, like, orari
    clean = re.sub(
        r"\b\d+[kKmM]?\b",
        "",
        clean
    )


    # elimina caratteri inutili
    clean = re.sub(
        r"[^\w\s@#]",
        " ",
        clean
    )


    # sistema spazi multipli
    clean = " ".join(
        clean.split()
    )


    unique_text = (
        f"{source}-{clean}"
    )


    hash_value = hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()


    return (
        f"x-{source}-{hash_value[:16]}"
    )
