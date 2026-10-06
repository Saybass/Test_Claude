"""Compila un documento per un cliente: preventivo, accordo o ricevuta.

Uso:
    python business/tools/genera_documento.py preventivo cliente.json

cliente.json contiene: "cliente", "indirizzo_cliente", "pacchetto" (Vetrina,
Completo o Tranquillità), "numero" (per preventivo e ricevuta) e, facoltativi,
"data" (predefinita: oggi), "prezzo" (predefinito: listino di config.json),
"ritenuta" (true se il cliente è un'impresa o un professionista) e
"id_fiscale_cliente" (P.IVA o C.F. del cliente).

Accordo e ricevuta richiedono anche --riservati: un file JSON con
"codice_fiscale" e "indirizzo" del titolare. Questi dati non stanno in
config.json, che è pubblico, ma nella pagina Notion «Dati riservati».

Il documento viene scritto in business/privato/<cliente>/<tipo>.html.
Quella cartella è esclusa da Git perché contiene dati dei clienti.
"""

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

from genera_demo import BUSINESS, carica_config, slug

TIPI = ("preventivo", "accordo", "ricevuta")
SOGLIA_BOLLO = 77.47

DESCRIZIONI = {
    "Vetrina": "sito di una pagina con presentazione, offerta, orari e contatti; pulsanti per WhatsApp, chiamata e mappa; "
               "adatto a telefono e computer; pubblicazione inclusa.",
    "Completo": "sito fino a 5 pagine (per esempio menu o listino, galleria, chi siamo, contatti); configurazione della "
                "scheda Google Business; modulo di contatto; pubblicazione inclusa.",
    "Tranquillità": "aggiornamento continuo di orari, menu e prezzi, con risposta entro 48 ore; canone mensile, "
                    "disdicibile in qualsiasi momento.",
}

STILE = """
  body { font: 15px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; color: #1d1b18;
         max-width: 760px; margin: 40px auto; padding: 0 24px; }
  header { display: flex; justify-content: space-between; align-items: flex-start;
           border-bottom: 3px solid #c2410c; padding-bottom: 16px; margin-bottom: 24px; }
  .logo { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
  .logo span { color: #c2410c; }
  .meta { text-align: right; color: #5f5a52; }
  .parti { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 8px; }
  h2 { font-size: 18px; margin: 28px 0 8px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 10px 0; border-bottom: 1px solid #e7e2d9; vertical-align: top; }
  .num { text-align: right; white-space: nowrap; }
  .totale td { font-weight: 800; font-size: 17px; border-bottom: 0; }
  .piccolo { color: #5f5a52; font-size: 13px; }
  .firme { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 48px; }
  @media print { body { margin: 0; } }
"""


def euro(importo):
    """290 -> '290,00'; 1234.5 -> '1.234,50'."""
    return f"{importo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dati_documento(tipo, cliente, config, oggi=None, riservati=None):
    pacchetto = cliente["pacchetto"]
    prezzo = float(cliente.get("prezzo") or config["prezzi"][pacchetto])
    dati = {k: v for k, v in config.items() if isinstance(v, str)}
    dati.update({k: str(v) for k, v in (riservati or {}).items()})
    dati.update({
        "cliente": cliente["cliente"],
        "indirizzo_cliente": cliente.get("indirizzo_cliente", ""),
        "pacchetto": pacchetto,
        "numero": str(cliente.get("numero", "")),
        "data": cliente.get("data") or (oggi or datetime.date.today()).strftime("%d/%m/%Y"),
        "descrizione_pacchetto": DESCRIZIONI.get(pacchetto, ""),
        "prezzo": euro(prezzo),
        "id_fiscale_cliente": cliente.get("id_fiscale_cliente", ""),
    })
    if tipo == "ricevuta":
        ritenuta = round(prezzo * 0.20, 2) if cliente.get("ritenuta") else 0.0
        dati.update({
            "lordo": euro(prezzo),
            "ritenuta": euro(ritenuta),
            "netto": euro(prezzo - ritenuta),
            "nota_bollo": "Imposta di bollo di 2 € assolta sull'originale." if prezzo > SOGLIA_BOLLO else "",
        })
    return dati


def compila(modello, dati):
    """Sostituisce i segnaposto {{chiave}}. Solleva KeyError se ne manca qualcuno."""
    mancanti = sorted({k for k in re.findall(r"\{\{(\w+)\}\}", modello) if k != "stile" and k not in dati})
    if mancanti:
        raise KeyError("Mancano questi dati: " + ", ".join(mancanti))
    return re.sub(
        r"\{\{(\w+)\}\}",
        lambda m: STILE if m.group(1) == "stile" else html.escape(dati[m.group(1)]),
        modello,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tipo", choices=TIPI)
    parser.add_argument("cliente", help="file JSON con i dati del cliente")
    parser.add_argument("--riservati", help="file JSON con codice fiscale e indirizzo del titolare")
    args = parser.parse_args(argv)

    cliente = json.loads(Path(args.cliente).read_text(encoding="utf-8"))
    modello = (BUSINESS / "documenti" / f"{args.tipo}.html").read_text(encoding="utf-8")
    riservati = json.loads(Path(args.riservati).read_text(encoding="utf-8")) if args.riservati else None
    try:
        documento = compila(modello, dati_documento(args.tipo, cliente, carica_config(), riservati=riservati))
    except KeyError as errore:
        sys.exit(errore.args[0])
    if "DA-COMPILARE" in documento:
        sys.exit("Completa prima business/config.json: il documento conterrebbe DA-COMPILARE.")

    destinazione = BUSINESS / "privato" / slug(cliente["cliente"]) / f"{args.tipo}.html"
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_text(documento, encoding="utf-8")
    print(destinazione.relative_to(BUSINESS.parent))


if __name__ == "__main__":
    main()
