# Insegna: siti web per attività locali, gestiti da agenti

Insegna vende siti web a prezzo fisso alle attività locali che non ne hanno uno. Due agenti automatici fanno tutto il lavoro ripetitivo. Il titolare interviene in due momenti: nelle chiamate con i clienti e nei casi che gli agenti segnalano come «Da vedere».

| Pacchetto | Prezzo | Cosa include |
| --- | --- | --- |
| Vetrina | 290 € | una pagina, pulsanti WhatsApp, chiamata e mappa, online in 5 giorni |
| Completo | 490 € | fino a 5 pagine, scheda Google Business, modulo di contatto |
| Tranquillità | 19 €/mese | aggiornamenti di orari, menu e prezzi |

Per arrivare a 1000 € bastano 2 Completo, oppure 4 Vetrina. I costi sono zero: i siti sono pubblicati gratis su GitHub Pages e il dominio lo paga il cliente.

## Come funziona

| Fase | Chi | Cosa succede |
| --- | --- | --- |
| Prospezione | Giro mattutino | Trova ogni giorno 5 attività della città senza sito e le aggiunge al CRM in Notion |
| Demo | Giro mattutino | Genera e pubblica un'anteprima gratuita del sito di ognuna |
| Primo contatto | Giro mattutino, poi **tu con un clic** | Prepara l'email personalizzata come bozza in Gmail (o il testo WhatsApp). Tu la invii |
| Risposte | Segreteria | Risponde a chi scrive, propone orari, manda il link di prenotazione |
| Appuntamenti | Segreteria | Crea o completa l'evento in Google Calendar, con link Meet e scheda di preparazione |
| Chiamata | **Tu** | Parli con il cliente e segni l'esito in Notion: Vinto con il pacchetto, oppure Perso |
| Preventivo | Segreteria | Manda preventivo, accordo e lista dei materiali |
| Consegna | Segreteria | Costruisce il sito definitivo, gestisce le modifiche, manda ricevuta e IBAN |
| Pagamento | **Tu** | Verifichi il bonifico e imposti Stato «Consegnato» |
| Agenda | Giro mattutino | Ogni mattina aggiorna l'agenda in Notion e ti manda il riepilogo per email |

### Perché il primo contatto richiede un clic

In Italia le email commerciali richiedono il consenso del destinatario (art. 130 del Codice Privacy), anche verso gli indirizzi aziendali pubblicati online. Per questo gli agenti preparano il primo messaggio come bozza e lo invii tu, dopo averlo letto. Da quel momento, chi risponde o prenota viene gestito in automatico. Chi dice no non viene più contattato.

## Dove sono le cose

- **Notion → «Insegna – Sede»** (pagina privata):
  - **Clienti**: il CRM, con le viste Pipeline (per stato) e Appuntamenti (calendario);
  - **Agenda**: il programma del giorno, aggiornato ogni mattina;
  - **Dati riservati**: codice fiscale, indirizzo e IBAN per accordi e ricevute.
- **Google Calendar**: gli appuntamenti iniziano con «Insegna · ».
- **Gmail**: bozze da inviare, etichette `Insegna/Gestito` e `Insegna/Da vedere`.
- **Questo repository**:
  - `config.json`: dati pubblici dell'azienda e impostazioni;
  - `agenti/`: istruzioni degli agenti (`regole.md`, `giro-mattutino.md`, `segreteria.md`) e testi dei messaggi (`messaggi.md`);
  - `sito/`: il sito di Insegna (pagina principale e privacy);
  - `demo/`: il sito di esempio e le anteprime generate per i contatti;
  - `clienti/`: i siti consegnati;
  - `brand/`: logo, favicon e firma email;
  - `documenti/`: modelli di preventivo, accordo e ricevuta;
  - `tools/`: generatori e controlli, con i test.

## Configurazione iniziale (una volta sola, circa 15 minuti)

1. **Compila `config.json`:** `titolare`, `email`, `telefono`, `whatsapp`, `citta`, `link_prenotazione`. Se preferisci, scrivi i dati a Claude in una sessione e li inserisce Claude.
2. **Crea la pagina di prenotazione:** in Google Calendar scegli **Crea → Programma di appuntamenti**, con durata di 30 minuti, i tuoi orari disponibili e il link Google Meet. Copia il link pubblico in `link_prenotazione`.
3. **Attiva GitHub Pages:** in GitHub apri **Settings → Pages** del repository, poi Source «Deploy from a branch», ramo `claude/quirky-galileo-0qjnag`, cartella `/ (root)`. Il sito sarà su `https://saybass.github.io/Test_Claude/business/sito/`.
4. **Compila «Dati riservati»** in Notion: codice fiscale, indirizzo e IBAN.
5. **Imposta la firma Gmail:** apri `brand/firma-email.html` nel browser, dopo che gli agenti hanno inserito i tuoi dati, e copiala in Gmail → Impostazioni → Firma.

Fino a quando config.json non è completo, gli agenti non contattano nessuno. Il giro mattutino ti manda solo un promemoria con i dati mancanti.

## Comandi utili

```bash
python business/tools/controlla_config.py                  # mancano dati?
python business/tools/applica_config.py                    # inserisce i dati nelle pagine pubbliche
python business/tools/genera_demo.py contatto.json         # anteprima in business/demo/<slug>/
python business/tools/genera_demo.py sito.json --finale    # sito del cliente in business/clienti/<slug>/
python business/tools/genera_documento.py preventivo cliente.json
python business/tools/genera_documento.py accordo cliente.json --riservati riservati.json
python business/tools/genera_documento.py ricevuta cliente.json --riservati riservati.json
cd business/tools && python -m unittest test_tools         # test
```

## Fisco

Finché l'attività è saltuaria puoi lavorare con la prestazione occasionale, senza partita IVA. Se il cliente è un'impresa, trattiene una ritenuta del 20% (la ricevuta la calcola da sola). Sopra i 77,47 € serve una marca da bollo da 2 €. Oltre i 5000 € l'anno scattano i contributi INPS. Se diventa un'attività continuativa serve la partita IVA. Fatti confermare tutto da un commercialista.
