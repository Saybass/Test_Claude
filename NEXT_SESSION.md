# Prossima sessione: automazioni Claude Code con `claude-code-setup`

Istruzioni per Claude. Eseguile in ordine, senza aspettare conferme, tranne dove è scritto di chiedere.

## 1. Verifica che il plugin sia attivo

Il passo deve superare tutti questi controlli:

1. Chiama `ListPlugins`: `claude-code-setup` deve comparire tra i plugin abilitati.
2. La skill `claude-automation-recommender` (anche con prefisso, es. `<id>:claude-automation-recommender`) deve comparire tra le skill che puoi invocare con lo strumento `Skill`.
3. `ls -R ~/.claude/plugins` deve mostrare i file del plugin nel container.

Riporta all'utente l'esito di ciascun controllo, una riga per controllo, con ✅ o ❌.

Se un controllo fallisce, **fermati**. Spiega all'utente cosa manca. Se il plugin è attivo sull'account ma non nel container, digli di aprire una nuova sessione. Non sostituire la skill con un'analisi fatta a mano.

## 2. Esegui la skill

Invoca `claude-automation-recommender` sull'intero repository: la CLI Python nella root e l'app Next.js in `studio/`. Prima di partire, leggi `studio/AGENTS.md`, `studio/layouts/AGENTS.md` e `studio/components/studio/AGENTS.md`.

## 3. Confronta con l'analisi precedente

Nella sessione precedente ho analizzato il repository a mano, senza il plugin. Ne sono uscite queste proposte:

- **Hook**
  - PreToolUse che blocca le modifiche a `studio/generation/catalog/models.generated.ts`, `studio/pnpm-lock.yaml` e `.env*` (escluso `.env.example`).
  - PostToolUse che esegue `prettier --write` sui file `studio/**/*.{ts,tsx}` modificati.
  - PostToolUse che esegue `node scripts/sync-models.mjs` (da `studio/`) quando cambia un file in `studio/generation/catalog/models/`.
  - SessionStart, solo in cloud, che esegue `pnpm install` in `studio/` e `pip install -r requirements.txt`, e imposta `NODE_USE_ENV_PROXY=1` tramite `CLAUDE_ENV_FILE`.
- **Skill**
  - `add-model`: aggiungere o correggere un modello del catalogo verificandolo contro la documentazione Higgsfield.
  - `verify-studio`: eseguire `pnpm typecheck && pnpm lint && pnpm test && pnpm build` e poi gli scenari di verifica di `studio/AGENTS.md` con Playwright.
- **Subagent**
  - `catalog-auditor` (sola lettura): confronta i modelli del catalogo con gli schemi documentati.
  - `boundary-reviewer`: controlla le regole "Runtime boundaries" di `studio/AGENTS.md`.
- **MCP**
  - context7, per la documentazione di Next 16, React 19, Tailwind 4 e vitest 5.
  - Playwright MCP, opzionale.
- **Root `CLAUDE.md`**: comando dei test Python, chiave in `.env.local`, `main.py` a pagamento (circa $2,31 per esecuzione).

Mostra all'utente una tabella sola con le raccomandazioni del plugin e queste. Per ciascuna indica se è proposta da entrambi, solo dal plugin o solo dall'analisi manuale, e la priorità.

## 4. Chiedi prima di implementare

Chiedi all'utente quali raccomandazioni implementare, con `AskUserQuestion` a scelta multipla. Implementa solo quelle scelte, in `.claude/` del repository. Prima di fare commit, verifica che ogni hook funzioni davvero: per esempio, prova a modificare `models.generated.ts` e controlla che l'hook lo blocchi. Poi fai commit e push sul branch della sessione.

## 5. Pulizia

A lavoro finito, elimina questo file (`NEXT_SESSION.md`) con un commit dedicato, così non viene eseguito di nuovo.
