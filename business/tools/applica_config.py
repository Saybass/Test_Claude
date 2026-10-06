"""Inserisce i dati di config.json nelle pagine pubbliche e nella firma email.

Sostituisce i segnaposto DA-COMPILARE-<CAMPO> nei file elencati in FILE.
Va eseguito una volta, dopo aver compilato config.json; gli agenti lo eseguono
da soli se trovano ancora segnaposto.
"""

import sys

from controlla_config import mancanti
from genera_demo import BUSINESS, carica_config, solo_cifre

FILE = ["sito/index.html", "sito/privacy.html", "brand/firma-email.html"]


def segnaposto(config):
    sito = config["sito_base_url"].rstrip("/") + "/business/sito/"
    return {
        "DA-COMPILARE-PRENOTAZIONE": config["link_prenotazione"],
        "DA-COMPILARE-EMAIL": config["email"],
        "DA-COMPILARE-WHATSAPP": solo_cifre(config.get("whatsapp") or config["telefono"]),
        "DA-COMPILARE-TELEFONO": config["telefono"],
        "DA-COMPILARE-TITOLARE": config["titolare"],
        "DA-COMPILARE-SITO": sito,
    }


def applica(testo, valori):
    for chiave, valore in valori.items():
        testo = testo.replace(chiave, valore)
    return testo


def main():
    config = carica_config()
    vuoti = mancanti(config)
    if vuoti:
        sys.exit("Mancano questi dati in business/config.json: " + ", ".join(vuoti))
    valori = segnaposto(config)
    for nome in FILE:
        percorso = BUSINESS / nome
        testo = percorso.read_text(encoding="utf-8")
        nuovo = applica(testo, valori)
        if nuovo != testo:
            percorso.write_text(nuovo, encoding="utf-8")
            print(f"Aggiornato business/{nome}")
        if "DA-COMPILARE" in nuovo:
            print(f"Attenzione: business/{nome} contiene ancora DA-COMPILARE")


if __name__ == "__main__":
    main()
