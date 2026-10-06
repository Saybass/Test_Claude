import datetime
import unittest

import applica_config
import controlla_config
import genera_demo
import genera_documento

CONFIG = {"brand": "Insegna", "link_prenotazione": "DA-COMPILARE", "sito_base_url": "DA-COMPILARE"}


class SlugTest(unittest.TestCase):
    def test_removes_accents_and_punctuation(self):
        self.assertEqual(genera_demo.slug("Caffè Città, Lecce!"), "caffe-citta-lecce")

    def test_empty_name_has_fallback(self):
        self.assertEqual(genera_demo.slug("***"), "attivita")


class PhoneTest(unittest.TestCase):
    def test_italian_mobile_gets_prefix(self):
        self.assertEqual(genera_demo.solo_cifre("333 123 4567"), "393331234567")

    def test_international_prefix_is_kept(self):
        self.assertEqual(genera_demo.solo_cifre("+39 0832 123456"), "390832123456")
        self.assertEqual(genera_demo.solo_cifre("0039 333 1234567"), "393331234567")


class GeneraTest(unittest.TestCase):
    def test_minimal_contact(self):
        nome, pagina = genera_demo.genera({"nome": "Bar Sport", "categoria": "Bar", "citta": "Lecce"}, CONFIG)
        self.assertEqual(nome, "bar-sport-lecce")
        self.assertIn("<h1>Bar Sport</h1>", pagina)
        self.assertIn('content="noindex, nofollow"', pagina)
        self.assertIn("Non è il sito ufficiale", pagina)
        self.assertIn("Questi sono esempi", pagina)
        self.assertNotIn("wa.me", pagina)
        self.assertNotIn("tel:", pagina)
        self.assertNotIn("DA-COMPILARE", pagina)
        self.assertNotIn("<h2>Orari</h2>", pagina)

    def test_full_contact(self):
        contatto = {
            "nome": "Forno Rossi", "categoria": "Forno", "citta": "Bari", "indirizzo": "Via Roma 1",
            "telefono": "080 123 4567", "whatsapp": "333 1234567",
            "orari": [["Lun–Sab", "7:00–13:00"]], "prodotti": [["Pane", "4 €"]],
        }
        cfg = dict(CONFIG, link_prenotazione="https://cal.example/insegna", sito_base_url="https://x.github.io/repo/")
        _, pagina = genera_demo.genera(contatto, cfg)
        self.assertIn('href="tel:+390801234567"', pagina)
        self.assertIn('href="https://wa.me/393331234567"', pagina)
        self.assertIn("<td>Lun–Sab</td><td>7:00–13:00</td>", pagina)
        self.assertIn("<span>Pane</span><span>4 €</span>", pagina)
        self.assertNotIn("Questi sono esempi", pagina)
        self.assertIn("https://cal.example/insegna", pagina)
        self.assertIn('href="https://x.github.io/repo/business/sito/"', pagina)

    def test_final_site_has_no_preview_marks(self):
        contatto = {"nome": "Bar Sport", "categoria": "Bar", "prodotti": [["Caffè", "1,20 €"]]}
        _, pagina = genera_demo.genera(contatto, CONFIG, finale=True)
        self.assertNotIn("noindex", pagina)
        self.assertNotIn("Anteprima", pagina)
        self.assertIn("<title>Bar Sport</title>", pagina)
        self.assertIn("Sito realizzato da Insegna", pagina)

    def test_text_is_escaped(self):
        _, pagina = genera_demo.genera({"nome": "<script>x</script>", "categoria": "Bar"}, CONFIG)
        self.assertNotIn("<script>", pagina)
        self.assertIn("&lt;script&gt;", pagina)

    def test_unknown_category_uses_default_theme(self):
        _, pagina = genera_demo.genera({"nome": "Studio Bianchi", "categoria": "Altro"}, CONFIG)
        self.assertIn("Cosa offriamo", pagina)


class ConfigTest(unittest.TestCase):
    def test_reports_missing_fields(self):
        self.assertEqual(
            controlla_config.mancanti({"titolare": "Ada", "email": "DA-COMPILARE", "telefono": ""}),
            ["email", "telefono", "citta", "link_prenotazione", "sito_base_url"],
        )


class DocumentoTest(unittest.TestCase):
    CONFIG = {"brand": "Insegna", "titolare": "Ada Rossi", "email": "ada@example.com", "telefono": "333",
              "prezzi": {"Vetrina": 290, "Completo": 490, "Tranquillità": 19}}
    RISERVATI = {"codice_fiscale": "RSSDAA90A41F205X", "indirizzo": "Via Verdi 2, Lecce"}
    CLIENTE = {"cliente": "Forno Rossi", "indirizzo_cliente": "Via Roma 1, Bari", "pacchetto": "Completo",
               "numero": "2026-001", "email": "forno@example.com"}

    def modello(self, tipo):
        return (genera_documento.BUSINESS / "documenti" / f"{tipo}.html").read_text(encoding="utf-8")

    def test_euro_format(self):
        self.assertEqual(genera_documento.euro(290), "290,00")
        self.assertEqual(genera_documento.euro(1234.5), "1.234,50")

    def test_all_templates_fill_without_missing_keys(self):
        for tipo in genera_documento.TIPI:
            dati = genera_documento.dati_documento(
                tipo, self.CLIENTE, self.CONFIG, datetime.date(2026, 10, 6), riservati=self.RISERVATI)
            documento = genera_documento.compila(self.modello(tipo), dati)
            self.assertNotIn("{{", documento, tipo)
            self.assertIn("Forno Rossi", documento)

    def test_client_fields_do_not_override_brand(self):
        dati = genera_documento.dati_documento("preventivo", self.CLIENTE, self.CONFIG, datetime.date(2026, 10, 6))
        self.assertEqual(dati["email"], "ada@example.com")
        self.assertEqual(dati["data"], "06/10/2026")
        self.assertEqual(dati["prezzo"], "490,00")

    def test_receipt_withholding_and_stamp(self):
        con = genera_documento.dati_documento("ricevuta", dict(self.CLIENTE, ritenuta=True), self.CONFIG)
        self.assertEqual((con["ritenuta"], con["netto"]), ("98,00", "392,00"))
        self.assertIn("bollo", con["nota_bollo"])
        senza = genera_documento.dati_documento("ricevuta", dict(self.CLIENTE, pacchetto="Tranquillità"), self.CONFIG)
        self.assertEqual((senza["ritenuta"], senza["netto"], senza["nota_bollo"]), ("0,00", "19,00", ""))

    def test_receipt_needs_private_data(self):
        dati = genera_documento.dati_documento("ricevuta", self.CLIENTE, self.CONFIG)
        with self.assertRaisesRegex(KeyError, "codice_fiscale"):
            genera_documento.compila(self.modello("ricevuta"), dati)

    def test_missing_key_is_reported(self):
        with self.assertRaisesRegex(KeyError, "numero"):
            genera_documento.compila("{{numero}}", {})

    def test_values_are_escaped(self):
        self.assertEqual(genera_documento.compila("{{cliente}}", {"cliente": "<b>"}), "&lt;b&gt;")


class ApplicaConfigTest(unittest.TestCase):
    def test_every_placeholder_in_public_files_is_known(self):
        config = {"sito_base_url": "https://x.github.io/repo", "link_prenotazione": "https://cal.example",
                  "email": "a@example.com", "telefono": "333 1234567", "titolare": "Ada Rossi"}
        valori = applica_config.segnaposto(config)
        self.assertEqual(valori["DA-COMPILARE-SITO"], "https://x.github.io/repo/business/sito/")
        self.assertEqual(valori["DA-COMPILARE-WHATSAPP"], "393331234567")
        for nome in applica_config.FILE:
            testo = (genera_demo.BUSINESS / nome).read_text(encoding="utf-8")
            self.assertNotIn("DA-COMPILARE", applica_config.applica(testo, valori), nome)


if __name__ == "__main__":
    unittest.main()
