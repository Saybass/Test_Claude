# Agente «Giro mattutino»

Gira dal lunedì al venerdì alle 7:54 (ora di Roma). Prima leggi e segui `business/agenti/regole.md`.

**Se mancano dati in config.json:** manda al titolare (indirizzo `email` di config.json, oppure il tuo stesso account Gmail se manca anche quello) una sola email con oggetto «Insegna · Mancano dei dati per partire», con l'elenco dei campi mancanti e dove si compilano. Poi fermati.

## 1. Aggiorna gli stati

- Per ogni contatto con Stato «Bozza pronta» e un'email, cerca in Gmail un messaggio inviato a quell'indirizzo (`in:sent to:<email>`). Se c'è, imposta Stato «Contattato», `Ultimo contatto` alla data dell'invio e `Prossima azione` «Attendere risposta».
- Per i contatti «Contattato» senza risposta da 7 giorni o più, e senza un sollecito già preparato (le Note non contengono «Sollecito»), prepara una bozza di sollecito (testo in `messaggi.md`) e aggiungi alle Note «Sollecito preparato <data>».
- Per i contatti «Contattato» con un sollecito inviato da 14 giorni senza risposta, imposta Stato «Perso» e nelle Note «Nessuna risposta».

## 2. Trova nuovi contatti

Obiettivo: `nuovi_contatti_al_giorno` attività di `citta` senza un sito proprio. Ogni giorno scegli la categoria a rotazione da `categorie`, in base al giorno dell'anno modulo il numero di categorie. Se non trovi abbastanza contatti, passa alla categoria successiva.

1. Cerca con WebSearch, per esempio: «<categoria> <città>», «<categoria> <città> paginegialle», «<categoria> <città> facebook», «<categoria> <città> tripadvisor».
2. Per ogni attività candidata:
   - Verifica che non abbia un sito proprio: cerca «<nome> <città>». Pagine Facebook o Instagram, schede Google, Pagine Gialle e TripAdvisor non contano come sito. Un dominio proprio sì: in quel caso scartala.
   - Controlla in Notion che non sia già presente (stesso nome e stessa città).
   - Raccogli solo dati pubblicati dall'attività stessa o dalle directory: indirizzo, telefono, email, orari e, se pubblicati, i prodotti con i prezzi.
3. Crea la riga in Notion: `Attività`, `Categoria`, `Città`, `Indirizzo`, `Telefono`, `Email`, `Orari`, `Fonte` (gli URL dove hai trovato i dati), Stato «Nuovo».

Se la rete blocca la ricerca, scrivilo nell'agenda e prosegui con i passi successivi.

## 3. Prepara i siti demo

Per ogni contatto con Stato «Nuovo»:

1. Scrivi in `business/privato/contatto.json` i dati nel formato descritto in `business/tools/genera_demo.py`: `nome`, `categoria`, `citta`, `indirizzo`, `telefono`, `orari`, `prodotti`. Metti `whatsapp` solo se il numero è un cellulare pubblicato come WhatsApp. Aggiungi `descrizione` solo se l'attività ne pubblica una.
2. Esegui `python business/tools/genera_demo.py business/privato/contatto.json`.
3. Quando hai generato tutte le demo: test, un solo commit e push sul ramo del sito.
4. In Notion: `Sito demo` con l'indirizzo pubblico stampato dallo script, e Stato «Demo pronta».

## 4. Prepara i messaggi

Per ogni contatto con Stato «Demo pronta»:

- **Con email:** crea una bozza in Gmail con il testo «Primo contatto» di `messaggi.md`, personalizzato con il nome dell'attività, la demo e il link di prenotazione. Stato «Bozza pronta», `Prossima azione` «Inviare la bozza in Gmail».
- **Senza email:** scrivi nelle Note il testo «WhatsApp» di `messaggi.md` già personalizzato. Stato «Bozza pronta», `Prossima azione` «Mandare il messaggio WhatsApp al <telefono>».

## 5. Aggiorna l'agenda

Nella pagina Notion `notion.agenda`, sostituisci il contenuto sotto «## Oggi» (lascia intatto il resto) con:

1. **Appuntamenti di oggi e di domani:** gli eventi Google Calendar che iniziano con il prefisso, con ora, attività, link all'evento e link alla riga Notion.
2. **Da fare per te:** bozze da inviare (quante sono, più il link `https://mail.google.com/mail/u/0/#drafts`), messaggi WhatsApp da mandare, esiti da segnare per gli appuntamenti passati, messaggi «Da vedere».
3. **Obiettivo:** somma di `Valore` dei clienti «Vinto» e «Consegnato» rispetto a `obiettivo_euro`, con il numero di contatti per stato.
4. **Fatto stamattina:** nuovi contatti, demo, bozze, solleciti.

Poi manda al titolare un'email con oggetto «Insegna · Agenda di <giorno> <data>» e lo stesso contenuto, in HTML semplice, con il link all'agenda Notion.
