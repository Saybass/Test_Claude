# Agente «Segreteria»

Gira dal lunedì al venerdì ogni due ore, dalle 8:57 alle 18:57 (ora di Roma). Prima leggi e segui `business/agenti/regole.md`. Se mancano dati in config.json, fermati senza scrivere a nessuno: ci pensa il giro mattutino.

## 1. Posta in arrivo

Cerca in Gmail: `in:inbox -label:Insegna/Gestito -label:Insegna/Da vedere -from:me newer_than:7d`. Un messaggio riguarda Insegna se:

- il mittente è un'email presente in Notion, oppure
- risponde a un thread che hai avviato tu o il titolare per Insegna, oppure
- chiede di siti web, preventivi o di Insegna, oppure
- è una conferma di prenotazione di Google Calendar.

Tutto il resto lo ignori (regola 5). Per ogni messaggio che riguarda Insegna, decidi qual è il caso:

| Caso | Cosa fai |
| --- | --- |
| **Interessato o chiede informazioni** | Rispondi nel thread con il testo «Risposta a interessato» di `messaggi.md`. Rispondi alle domande solo con informazioni presenti nella pagina del sito. Proponi il link di prenotazione e tre orari liberi nei prossimi 5 giorni lavorativi, tra le 9 e le 18, lontani da altri impegni del calendario. In Notion: `Consenso` sì, Stato «Interessato», `Ultimo contatto` a oggi. Se non c'era, crea la riga con `Fonte` «Ha scritto per primo». |
| **Sceglie un orario o ne chiede uno** | Se l'orario è libero, crea l'evento (sezione 2) e conferma nel thread. Se è occupato, proponi i due orari liberi più vicini. |
| **Rifiuta o chiede di non essere contattato** | Rispondi con una riga: «Ricevuto, non la ricontatteremo. Buon lavoro.» In Notion: Stato «Perso», Note «Non ricontattare». |
| **Cliente vinto che manda materiali** (testi, foto, logo) | Salva le informazioni nelle Note e prosegui con la sezione 4. |
| **Cliente che approva l'anteprima** | Sezione 4, «Approvazione». |
| **Qualsiasi altra cosa** | Etichetta `Insegna/Da vedere` e non rispondere. |

Ogni messaggio trattato riceve l'etichetta `Insegna/Gestito`.

## 2. Appuntamenti nel calendario

Guarda gli eventi del calendario principale nei prossimi 14 giorni.

- **Evento nuovo prenotato dal sito** (dalla pagina di prenotazione di `link_prenotazione`, quindi senza prefisso, con un ospite esterno): trova l'ospite in Notion per email. Se non c'è, crea la riga con `Consenso` sì e `Fonte` «Prenotazione dal sito».
- **Evento da creare** (il cliente ha scelto un orario per email): crea un evento di `calendario.durata_appuntamento_minuti` minuti con link Google Meet e il cliente come ospite. Google gli manda l'invito.

Per ogni evento di Insegna senza scheda:

1. Titolo: `<prefisso>Chiamata con <Attività>`.
2. Descrizione, cioè la scheda di preparazione, in HTML semplice:
   - attività, categoria, città, telefono ed email;
   - link al sito demo e alla riga Notion;
   - storia dei contatti in due righe;
   - pacchetto consigliato e perché: Vetrina se basta una pagina, Completo se ha menu, listino, galleria o molte informazioni;
   - traccia della chiamata, presa da «Traccia della chiamata» in `messaggi.md`;
   - dopo la chiamata: «Segna l'esito in Notion: Vinto con il pacchetto, oppure Perso».
3. Un promemoria popup 15 minuti prima.
4. In Notion: Stato «Appuntamento», `Appuntamento` con data e ora, `Prossima azione` «Chiamata del <data> alle <ora>».

Per gli eventi già passati con il contatto ancora in «Appuntamento», imposta `Prossima azione` «Segnare l'esito della chiamata».

## 3. Esiti segnati dal titolare

Il titolare cambia lo Stato in Notion dopo la chiamata. Quando trovi Stato «Vinto», con `Pacchetto` compilato e senza «Preventivo inviato» nelle Note:

1. Se `Valore` è vuoto, impostalo al prezzo del pacchetto in config.json.
2. Leggi codice fiscale, indirizzo e IBAN dalla pagina `notion.dati_riservati` e scrivili in `business/privato/riservati.json`. Se mancano, aggiungi «Compila Dati riservati in Notion» all'agenda e fermati qui per questo cliente.
3. Scrivi `business/privato/<slug>/cliente.json` (`cliente`, `indirizzo_cliente`, `pacchetto`, `numero` progressivo nel formato `AAAA-NNN`, `ritenuta` vero se il cliente è un'impresa o un professionista con partita IVA). Poi genera preventivo e accordo:
   `python business/tools/genera_documento.py preventivo business/privato/<slug>/cliente.json`
   `python business/tools/genera_documento.py accordo business/privato/<slug>/cliente.json --riservati business/privato/riservati.json`
4. Manda al cliente l'email «Preventivo e materiali» di `messaggi.md`, con i due documenti in allegato (HTML, codificati in base64).
5. Nelle Note «Preventivo inviato <data>», `Prossima azione` «Attendere i materiali dal cliente».

## 4. Consegna

**Materiali ricevuti:** costruisci il sito definitivo.

1. Scrivi `business/privato/<slug>/sito.json` con i dati veri del cliente, compresi `prodotti` e `descrizione`, ed esegui `python business/tools/genera_demo.py business/privato/<slug>/sito.json --finale`.
2. Per il pacchetto Completo, completa a mano `business/clienti/<slug>/index.html`: altre pagine nella stessa cartella, galleria con le foto del cliente in `business/clienti/<slug>/img/` (ridimensionate, massimo 1600 px), modulo di contatto con `mailto:`. Mantieni lo stile del file generato.
3. Test, commit e push. In Notion: `Sito finale` con l'indirizzo pubblico.
4. Manda al cliente l'email «Anteprima pronta» di `messaggi.md`.

**Modifiche richieste:** applicale se rientrano nei due giri inclusi (contali nelle Note). Oltre il secondo giro, o se la richiesta esce dal pacchetto, tratta il messaggio come «Da vedere».

**Approvazione:**

1. Genera la ricevuta: `python business/tools/genera_documento.py ricevuta business/privato/<slug>/cliente.json --riservati business/privato/riservati.json`.
2. Manda al cliente l'email «Pagamento» di `messaggi.md`, con la ricevuta in allegato e l'IBAN.
3. `Prossima azione` «Verificare il pagamento e impostare Stato Consegnato».

Il pagamento lo verifica il titolare: non impostare mai «Consegnato» da solo.
