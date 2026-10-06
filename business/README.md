# Insegna: siti web per attività locali

Obiettivo: 1000 € di ordini senza spendere niente.

## L'idea

Molte attività locali (bar, forni, parrucchieri, artigiani, B&B) non hanno un sito, oppure ne hanno uno vecchio che non funziona sul telefono. Insegna vende loro un sito semplice a prezzo fisso:

| Pacchetto | Prezzo | Cosa include |
| --- | --- | --- |
| Vetrina | 290 € | una pagina, pulsanti WhatsApp, chiamata e mappa, online in 5 giorni |
| Completo | 490 € | fino a 5 pagine, scheda Google Business, modulo di contatto |
| Tranquillità | 19 €/mese | aggiornamenti di orari, menu e prezzi |

Per arrivare a 1000 € bastano **2 Completo**, oppure **4 Vetrina**, oppure 2 Vetrina e 1 Completo.

Costi: 0 €. I siti sono HTML statico, pubblicati gratis su GitHub Pages, Netlify o Cloudflare Pages. Il dominio lo paga il cliente (10–15 € l'anno) ed è intestato a lui. Il codice lo scrive Claude: tu porti i clienti, raccogli testi e foto, e incassi.

## Cosa c'è in questa cartella

- `sito/index.html`: la pagina di Insegna, con prezzi e contatti. Prima di pubblicarla sostituisci `TUA-EMAIL` e `TUO-NUMERO`.
- `demo/index.html`: il sito di un forno inventato, da mostrare ai clienti come esempio.

## Pubblicare gratis

1. Su GitHub apri **Settings → Pages** di questo repository.
2. Scegli il branch e la cartella. Il sito sarà su `https://<utente>.github.io/<repo>/business/sito/`.

Netlify e Cloudflare Pages fanno lo stesso: trascini la cartella e il sito è online.

## Come trovare i clienti

In ordine di efficacia:

1. **Di persona.** Entra in 10 attività del tuo quartiere che non hanno un sito, con la demo aperta sul telefono. Di solito è il canale che converte di più.
2. **Al telefono.** Chiama le attività che su Google Maps non hanno un sito.
3. **Annunci gratuiti** su Subito.it (Servizi), Facebook Marketplace e i gruppi locali, e un profilo su Fiverr o Malt. Qui sono i clienti a contattarti.
4. **Passaparola.** Offri 50 € di sconto a ogni cliente che ti presenta un'altra attività.

Come trovarle su Google Maps: cerca "panificio", "parrucchiere", "bar" e simili nella tua città. Le schede senza il pulsante **Sito web** sono i tuoi contatti.

### Attenzione alle email a freddo

In Italia, per mandare email commerciali serve il consenso del destinatario (art. 130 del Codice Privacy). Questo vale anche per gli indirizzi aziendali pubblicati online. Per questo il piano punta su visite di persona, telefonate e annunci, e Claude non ha mandato email di massa a tuo nome. Rispondere a chi ti scrive per primo, o a chi ti ha dato il suo contatto, va benissimo.

Per le telefonate: verifica che il numero non sia iscritto al Registro pubblico delle opposizioni.

## Testi pronti

### Di persona (30 secondi)

> Buongiorno, mi chiamo ___ e faccio siti web per le attività della zona. Ho visto che su Google non avete un sito: chi vi cerca trova solo l'indirizzo. Le faccio vedere un esempio? *(mostra la demo)* In 5 giorni potete avere un sito così, con orari, prodotti e un pulsante per scrivervi su WhatsApp. Costa 290 € una volta sola, e si paga solo quando il sito vi piace. Le lascio il mio numero?

### Al telefono

> Buongiorno, sono ___. Faccio siti per le attività di [città]. Vi ho cercati su Google Maps e ho visto che non avete un sito. Posso mandarvi su WhatsApp un esempio di quello che faccio? Se vi interessa ne parliamo, altrimenti nessun problema.

### WhatsApp, dopo che ti hanno detto sì

> Ciao, sono ___, ci siamo sentiti poco fa. Ecco l'esempio: [link alla demo]. Per voi farei una pagina con chi siete, i vostri prodotti, gli orari e i pulsanti per chiamarvi e trovarvi. 290 €, online in 5 giorni, e paghi solo quando il sito ti piace. Ti va di mandarmi qualche foto e il testo che vorresti?

### Annuncio su Subito.it o Facebook Marketplace

> **Titolo:** Sito web per la tua attività a 290 €, online in 5 giorni
>
> Creo siti semplici e veloci per bar, ristoranti, negozi, artigiani e B&B.
> - Perfetto su telefono e computer
> - Pulsanti per WhatsApp, chiamata e indicazioni stradali
> - Orari, prodotti o menu sempre aggiornati
> - Prezzo fisso, paghi solo quando il sito ti piace
>
> Esempio: [link alla demo]. Scrivimi per un preventivo gratuito.

### Gig su Fiverr o Malt

> **Titolo:** Creo un sito vetrina moderno per la tua attività locale
>
> Ti consegno un sito veloce e adatto ai telefoni, con i tuoi testi e le tue foto: chi sei, cosa offri, orari, mappa e pulsanti di contatto. Pubblicazione inclusa, nessun abbonamento obbligatorio.

## Come consegnare un sito

1. Raccogli: nome dell'attività, logo (se c'è), 5–10 foto, prodotti e prezzi, orari, indirizzo, telefono, WhatsApp.
2. Chiedi a Claude: "Crea il sito per [attività] usando `business/demo/` come base, con questi dati: …".
3. Pubblica l'anteprima gratis e manda il link al cliente.
4. Fai le modifiche richieste.
5. Collega il dominio del cliente e incassa.

## Fisco

Se lo fai saltuariamente puoi lavorare con la prestazione occasionale, senza partita IVA. Se il cliente è un'impresa, di solito trattiene una ritenuta del 20%. Oltre i 5000 € l'anno scattano i contributi INPS. Se diventa un'attività continuativa serve la partita IVA. Chiedi conferma a un commercialista.
