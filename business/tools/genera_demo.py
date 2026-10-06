"""Genera un sito demo personalizzato per un contatto di Insegna.

Uso:
    python business/tools/genera_demo.py contatto.json

Il file JSON descrive l'attività. Campi obbligatori: "nome", "categoria".
Facoltativi: "citta", "indirizzo", "telefono", "whatsapp", "email",
"descrizione", "orari" (testo, oppure lista di coppie [giorni, ore]) e
"prodotti" (lista di coppie [nome, prezzo]).

Il sito viene scritto in business/demo/<slug>/index.html. Con --finale
genera il sito definitivo del cliente, senza la fascia «Anteprima», in
business/clienti/<slug>/index.html. Lo script stampa il percorso e, se
config.json ha "sito_base_url", l'indirizzo pubblico.
"""

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

BUSINESS = Path(__file__).resolve().parent.parent
DA_COMPILARE = "DA-COMPILARE"

# Aspetto e testi di ogni categoria. Gli esempi servono solo a mostrare dove
# andranno i prodotti veri: nella pagina sono marcati come esempi.
TEMI = {
    "Bar": {"accento": "#0f766e", "sfondo": "#f6fbfa", "font": "system-ui, sans-serif",
            "sezione": "Menu", "esempi": [["Caffè espresso", "1,20 €"], ["Cappuccino", "1,60 €"], ["Aperitivo", "6 €"]]},
    "Ristorante": {"accento": "#9f1239", "sfondo": "#fdf7f8", "font": "Georgia, serif",
                   "sezione": "Menu", "esempi": [["Antipasto della casa", "9 €"], ["Primo del giorno", "12 €"], ["Dolce", "6 €"]]},
    "Forno": {"accento": "#8a4b14", "sfondo": "#fffaf2", "font": "Georgia, serif",
              "sezione": "I nostri prodotti", "esempi": [["Pane casereccio (1 kg)", "4,50 €"], ["Focaccia", "14 €/kg"], ["Cornetto", "1,30 €"]]},
    "Parrucchiere": {"accento": "#6d28d9", "sfondo": "#faf8ff", "font": "system-ui, sans-serif",
                     "sezione": "Servizi e prezzi", "esempi": [["Taglio", "20 €"], ["Piega", "15 €"], ["Colore", "da 35 €"]]},
    "Estetica": {"accento": "#be185d", "sfondo": "#fff7fb", "font": "system-ui, sans-serif",
                 "sezione": "Trattamenti", "esempi": [["Pulizia del viso", "45 €"], ["Manicure", "20 €"], ["Massaggio (50 min)", "50 €"]]},
    "Negozio": {"accento": "#1d4ed8", "sfondo": "#f7f9ff", "font": "system-ui, sans-serif",
                "sezione": "Cosa trovi da noi", "esempi": [["Novità della stagione", ""], ["Idee regalo", ""], ["Ordini su richiesta", ""]]},
    "Artigiano": {"accento": "#b45309", "sfondo": "#fffbf5", "font": "system-ui, sans-serif",
                  "sezione": "Lavori e servizi", "esempi": [["Sopralluogo e preventivo", "gratuito"], ["Riparazioni", ""], ["Lavori su misura", ""]]},
    "B&B": {"accento": "#15803d", "sfondo": "#f7fcf8", "font": "Georgia, serif",
            "sezione": "Camere", "esempi": [["Camera doppia", "da 80 €/notte"], ["Camera singola", "da 55 €/notte"], ["Colazione", "inclusa"]]},
}
TEMA_PREDEFINITO = {"accento": "#c2410c", "sfondo": "#fbfaf7", "font": "system-ui, sans-serif",
                    "sezione": "Cosa offriamo", "esempi": [["Il vostro primo servizio", ""], ["Il secondo", ""], ["Il terzo", ""]]}


def slug(testo):
    """Trasforma un testo in un nome di cartella sicuro: 'Bar Sport, Lecce' -> 'bar-sport-lecce'."""
    ascii_ = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-") or "attivita"


def carica_config():
    return json.loads((BUSINESS / "config.json").read_text(encoding="utf-8"))


def valore(config, chiave):
    """Il valore di config.json, oppure None se non è ancora stato compilato."""
    v = config.get(chiave)
    return None if v in (None, "", DA_COMPILARE) else v


def solo_cifre(numero):
    cifre = re.sub(r"\D", "", numero or "")
    if cifre.startswith("00"):
        cifre = cifre[2:]
    if len(cifre) in (9, 10) and not cifre.startswith("39"):
        cifre = "39" + cifre  # numero italiano senza prefisso internazionale
    return cifre


def righe_orari(orari):
    if not orari:
        return ""
    if isinstance(orari, str):
        return f'<p>{html.escape(orari)}</p>'
    righe = "".join(f"<tr><td>{html.escape(g)}</td><td>{html.escape(o)}</td></tr>" for g, o in orari)
    return f"<table>{righe}</table>"


def schede_prodotti(prodotti, esempi):
    if prodotti:
        voci, classe, nota = prodotti, "item", ""
    else:
        voci, classe = esempi, "item esempio"
        nota = '<p class="nota">Questi sono esempi: nel sito vero ci saranno i vostri prodotti e i vostri prezzi.</p>'
    schede = "".join(
        f'<div class="{classe}"><span>{html.escape(n)}</span><span>{html.escape(p)}</span></div>'
        for n, p in voci
    )
    return f'<div class="menu">{schede}</div>{nota}'


def genera(contatto, config, finale=False):
    """Restituisce (slug, html) del sito demo, o di quello definitivo se finale è vero."""
    nome = contatto["nome"].strip()
    categoria = contatto.get("categoria", "Altro")
    tema = TEMI.get(categoria, TEMA_PREDEFINITO)
    citta = contatto.get("citta", "")
    indirizzo = contatto.get("indirizzo", "")
    brand = config.get("brand", "Insegna")

    pulsanti = []
    if contatto.get("telefono"):
        pulsanti.append(f'<a class="btn" href="tel:+{solo_cifre(contatto["telefono"])}">Chiama</a>')
    if contatto.get("whatsapp"):
        pulsanti.append(f'<a class="btn" href="https://wa.me/{solo_cifre(contatto["whatsapp"])}">WhatsApp</a>')
    luogo = " ".join(x for x in (nome, indirizzo, citta) if x)
    pulsanti.append(
        f'<a class="btn" href="https://www.google.com/maps/search/?api=1&amp;query={quote(luogo)}">Indicazioni</a>'
    )

    descrizione = contatto.get("descrizione") or (
        f"{categoria} a {citta}" if citta and categoria in TEMI else citta
    )
    dove = ", ".join(x for x in (indirizzo, citta) if x)
    sezione_orari = (
        f'<section><h2>Orari</h2>{righe_orari(contatto["orari"])}</section>' if contatto.get("orari") else ""
    )
    sezione_dove = f"<section><h2>Dove siamo</h2><p>{html.escape(dove)}</p></section>" if dove else ""

    prenota = valore(config, "link_prenotazione")
    invito = (
        f' <a href="{html.escape(prenota)}">Prenota una chiamata gratuita</a> per averlo così.' if prenota else ""
    )
    sito_brand = valore(config, "sito_base_url")
    firma = (
        f'<a href="{html.escape(sito_brand.rstrip("/"))}/business/sito/">{html.escape(brand)}</a>'
        if sito_brand else html.escape(brand)
    )

    if finale:
        robots, titolo, fascia, credito = "", html.escape(nome), "", "Sito realizzato da"
    else:
        robots = '<meta name="robots" content="noindex, nofollow">\n'
        titolo = f"{html.escape(nome)} · Anteprima"
        fascia = (
            f'<div class="ribbon">Anteprima gratuita preparata da {html.escape(brand)} per {html.escape(nome)}. '
            f"Non è il sito ufficiale dell'attività.{invito}</div>\n"
        )
        credito = "Anteprima realizzata da"

    pagina = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robots}<title>{titolo}</title>
<style>
  :root {{ --bg: {tema["sfondo"]}; --surface: #ffffff; --text: #1f1b16; --muted: #625a50;
          --accent: {tema["accento"]}; --accent-text: #ffffff; --line: #e8e1d6; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #16130f; --surface: #211d18; --text: #f4eee6; --muted: #bcb2a5;
            --accent-text: #ffffff; --line: #383128; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text); font: 17px/1.6 {tema["font"]}; }}
  .ribbon {{ background: var(--text); color: var(--bg); text-align: center; font: 14px/1.5 system-ui, sans-serif; padding: 8px 16px; }}
  .ribbon a {{ color: inherit; }}
  .wrap {{ max-width: 880px; margin: 0 auto; padding: 0 16px; }}
  .hero {{ text-align: center; padding: 64px 0 40px; }}
  h1 {{ font-size: clamp(34px, 7vw, 58px); line-height: 1.1; margin: 0 0 10px; }}
  .tag {{ color: var(--muted); font-size: 20px; margin: 0 0 28px; }}
  .actions {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; font-family: system-ui, sans-serif; }}
  .btn {{ background: var(--accent); color: var(--accent-text); padding: 12px 20px; border-radius: 999px; text-decoration: none; font-weight: 600; }}
  section {{ padding: 36px 0; border-top: 1px solid var(--line); }}
  h2 {{ font-size: 28px; margin: 0 0 16px; }}
  .menu {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
  .item {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; display: flex; justify-content: space-between; gap: 12px; }}
  .item span:last-child {{ font-weight: 700; white-space: nowrap; }}
  .esempio {{ border-style: dashed; opacity: .8; }}
  .nota {{ color: var(--muted); font-size: 15px; font-family: system-ui, sans-serif; }}
  table {{ width: 100%; border-collapse: collapse; font-family: system-ui, sans-serif; }}
  td {{ padding: 8px 0; border-bottom: 1px solid var(--line); }}
  td:last-child {{ text-align: right; }}
  footer {{ padding: 28px 0 48px; color: var(--muted); font-size: 15px; border-top: 1px solid var(--line); }}
  footer a {{ color: inherit; }}
</style>
</head>
<body>
{fascia}<div class="wrap">
  <div class="hero">
    <h1>{html.escape(nome)}</h1>
    <p class="tag">{html.escape(descrizione)}</p>
    <div class="actions">{"".join(pulsanti)}</div>
  </div>
  <section><h2>{html.escape(tema["sezione"])}</h2>{schede_prodotti(contatto.get("prodotti"), tema["esempi"])}</section>
  {sezione_orari}
  {sezione_dove}
  <footer>{html.escape(nome)} · {credito} {firma}</footer>
</div>
</body>
</html>
"""
    return slug(f"{nome} {citta}"), pagina


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("contatto", help="file JSON con i dati dell'attività")
    parser.add_argument("--finale", action="store_true", help="sito definitivo del cliente, senza fascia Anteprima")
    args = parser.parse_args(argv)

    contatto = json.loads(Path(args.contatto).read_text(encoding="utf-8"))
    if not contatto.get("nome"):
        sys.exit("Il contatto non ha un nome.")
    config = carica_config()
    nome_cartella, pagina = genera(contatto, config, finale=args.finale)

    cartella = "clienti" if args.finale else "demo"
    destinazione = BUSINESS / cartella / nome_cartella / "index.html"
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_text(pagina, encoding="utf-8")
    print(destinazione.relative_to(BUSINESS.parent))
    base = valore(config, "sito_base_url")
    if base:
        print(f"{base.rstrip('/')}/business/{cartella}/{nome_cartella}/")


if __name__ == "__main__":
    main()
