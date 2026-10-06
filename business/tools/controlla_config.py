"""Controlla che config.json sia compilato. Esce con codice 1 se mancano dati.

Gli agenti lo eseguono prima di ogni giro: se mancano dati non contattano nessuno.
"""

import json
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config.json"
OBBLIGATORI = ["titolare", "email", "telefono", "citta", "link_prenotazione", "sito_base_url"]


def mancanti(config):
    return [k for k in OBBLIGATORI if config.get(k) in (None, "", "DA-COMPILARE")]


def main():
    vuoti = mancanti(json.loads(CONFIG.read_text(encoding="utf-8")))
    if vuoti:
        print("Mancano questi dati in business/config.json: " + ", ".join(vuoti))
        sys.exit(1)
    print("config.json è completo.")


if __name__ == "__main__":
    main()
