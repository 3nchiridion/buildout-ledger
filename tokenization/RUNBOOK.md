# Daily run: The Tokenization Buildout Ledger

One pass of the loop: **collect → add rows → build → verify → gate (flag only) → publish → report.** Everything lives in this folder (`tokenization/`) of `3nchiridion/buildout-ledger`, served at buildoutledger.com/tokenization. The same files are also published as a Claude artifact (slug `7c67ebb2-b552-42fa-9b3f-434f364d4d86`).

## Rules that never bend

- **Touch only `tokenization/`.** The repo root, `raw/`, `edition/` and everything else belong to the AI Buildout Ledger, which is never modified. Never touch any other artifact.
- **Do not change the page.** `index.html`, `page_patch.py.txt` and `bs_view.js.txt` change only when Derek asks. A daily run changes data: `raw/declared.json`, `raw/readings.csv`, `ledger.json`, `verification.json`, and optionally `og.png`.
- **Every figure carries a source, a grade, an as-of date and a definition.** Grades: `onchain` (a public explorer read), `attested` (an accountant's report), `filed` (a regulator or SEC document), `announced` (the company's own page or release, or a wire copy of it), `reported` (press only; shown, never counted), `estimate`.
- **Primary sources first.** Trackers and dashboards (rwa.xyz, Token Terminal, DefiLlama and the like) only show where to look; they are never a source for a row.
- **One row cites one page, and every clause in the row must be on that page.** Do not add facts from a second page; make a second row or a gap note. For a long order or rule, state what it does and point to it for the conditions instead of summarising them.
- **Keyless public sources only.** The shell cannot reach outside sites; use WebFetch and WebSearch. If a page refuses automated reading, do not work around it (no mirrors of a blocked page, no caches): record it under `gaps`.
- **The collector (since 15 Nov 2026, approved by Derek).** `.github/workflows/tokenization-collect.yml` runs daily at 01:30 UTC, reads every entry in `tokenization/collect/registry.json` over public, keyless explorers and RPCs, and commits the raw responses to the `collect` branch (never `main`). Every address in the registry comes from the issuer's own release, page or registry API, named in `address_source`. A daily run may add or fix registry entries (inside `tokenization/`); it never edits the workflow file.
- **Never retype a number from memory.** Copy figures from what the page shows; show the arithmetic in the row's note when a value is derived.
- **History is append-only.** A changed row is corrected, and the change is logged in `corrections` ({date, rows, note}). The one exception is the on-chain history rule built into `tools/add_reading.py`: within a month, a new on-chain reading replaces the previous same-month one unless the value moved 10% or more.
- **The gate flags; it never holds.** Flagged updates publish, and the flags go into `gate_log`.
- **Materiality:** money tokens from $1B outstanding; assets from $250M; deals at $250M or when the counterparty is a top-ten issuer, a global bank or one of the six regulators (US, EU, UK, Hong Kong, Singapore, UAE). Retail CBDCs, wrapped BTC, staking tokens and crypto ETFs are out. Crypto-collateralised dollars (USDe, USDS) are shown, not counted.

## 1. Setup

1. Attach the repo with push access (`add_repo`, owner `3nchiridion`, repo `buildout-ledger`, access `push`), clone it, and work in its `tokenization/` folder.
2. Today = the current date in America/New_York. Run id = `run-<today>`.
3. Keep the baseline for the gate: `cp tokenization/ledger.json /tmp/live-ledger.json`.

## 2. Collect balances

0. **Collector snapshots first.** `git fetch origin +refs/heads/collect:refs/remotes/origin/collect`, then take the newest folder from `git ls-tree --name-only origin/collect snapshots/` (the collector runs at 01:30 UTC, so the folder carries the next UTC day; readings are dated in New York time) and check its `log.txt`. `python3 tokenization/tools/from_snapshots.py <folder> --dry-run` shows the readings it would add; run it without `--dry-run` to add them through `add_reading.py`. A FAIL line in the log is a gap for that day, not a reason to use another source. USTB is still valued by hand (shares from the snapshot times Superstate's NAV). Pack every new observation for the verifier with its evidence: `git show origin/collect:snapshots/<folder>/<id>.json`.
1. `python3 tokenization/tools/watchlist.py` lists every (token, chain) the ledger tracks whose next read is due, with the URL and how the last reading was made. Skip any the collector already read today.
2. **On-chain not in the registry (due every run):** WebFetch the same explorer URL. Take the same field as before (total supply, or the issuing account's obligations on the XRP Ledger), apply the token's decimals, and value it by the same rule as the previous reading's note: dollar tokens at $1 a token; fund shares at shares times the latest net asset value per share the fund's own page gives, or the derivation the note describes; a token count with no stated value stays a token count. Add it with `tools/add_reading.py`, using the same basis, method, source title and URL, and a note with the raw figure and decimals.
3. **Issuer pages (due after 3 days):** WebFetch the page. If it shows a newer date or figure, add a reading with that date as `as_of`, grade `announced`.
4. **Attestations (due 30 days after the latest as-of):** open the issuer's transparency or reserves page. If a newer report is out, read it and add: the total (grade `attested`), its per-chain amounts, the reserve metric, and backing rows that sum exactly to the reserves, following the token's existing rows in `raw/declared.json` (`metrics`, `backing`). Check the reconciliations the harness runs.
5. **Fund filings (due 30 days after the latest as-of):** WebFetch the `data.sec.gov` submissions URL in `raw/declared.json` `watchlist` for the fund. A newer N-MFP3 or N-CSR(S) for the token class is read from the filing itself (grade `filed`).
6. **Pending closes:** for each entry in `pending_close`, check the buyer's newsroom and SEC filings. On a primary-sourced close, append a revision to the flow with the new status and remove the entry. A press report alone is graded `reported` and changes nothing else.
7. **Gaps:** revisit the `gaps` that name a missing figure (xStocks' size, Ondo Stocks after August, Robinhood Stock Tokens' size). Fill one only from a primary source.

## 3. New rows

1. WebSearch for what has happened since the latest dated row (newest `date` in `flows`, `events` and `gate_log`): rules, approvals and charters in the six regimes; launches and new tokens crossing materiality; acquisitions and investments; custody, reserve and distribution ties for tokens already on the map; tokenized stocks, funds and deposits as well as dollar tokens.
2. Add each as a flow (tie or deal) or event in `raw/declared.json`, copying the fields of existing rows exactly (`id, payer, payee, type, status, amount_usd, amount_qualifier, date, grade, definition, source_title, source_url, level, title, label`; events: `id, date, entities, flow, level, title, detail, grade, source_title, source_url`). A new player or token is added to `entities` in the same pass, with the fields existing rows use; a new token needs `asset_class`, `counted` and a `wrapper` {regime, label}. A new chain is a `ledger` entity, and a token's chains go in `chains_listed`.
3. Statuses: `cash_moved` (live or closed), `contracted` (signed, not closed), `announced` (announced or conditional), `reported` (press only).
4. A signed deal that has not closed goes in `pending_close`.
5. Read the artifact's comments (`read_comments`). A comment that names a row and a contradicting source is a correction request: check it against the source, fix the row if it is right, and log it in `corrections`.

## 4. Build

`python3 tokenization/harness.py.txt --raw tokenization/raw build --asof <today> --run-id run-<today> --out tokenization/ledger.json`, then `python3 tokenization/harness.py.txt --raw tokenization/raw validate tokenization/ledger.json`. If either fails, fix the input rows (never weaken the validator) or remove the offending new row and record it under `gaps`, then rebuild.

## 5. Verify (independent)

1. List every id added or changed this run (new or replaced observations `o-<token>-<chain>-<date>`, flows, events, backing rows, metrics, and `ent-<id>` for a new token's wrapper label and note), plus every id in `verification_pending`.
2. `python3 tokenization/tools/pack_rows.py /tmp/rows-<today>.json --pending <ids...>`
3. Spawn one separate general-purpose agent that has not seen your work, with this prompt (fill in the paths):

   > You are an independent checker for a public data ledger about tokenization. You have not seen how these rows were made; check them only against their cited sources. Input: `/tmp/rows-<today>.json`, a list of groups {source_url, rows}. Open each source with WebFetch (the shell cannot reach the web; PDFs can be read with WebFetch; page long documents with the offset parameter). For every row decide "confirmed" (every element is supported: who, relationship, amount, date, legal form, chain, and each clause of the definition, detail, note or label), "finding" (anything unsupported, overstated, missing a qualifier or misattributed; say what, quoting the page in under 20 words) or "unreadable" (say why; do not guess). Grades: "filed" needs an official government document; "announced" a company's own page or release (a mirror only if it carries the company's own release text; say whether it does); "attested" an accountant's report; "onchain" an explorer read. For on-chain rows, check that the URL is the explorer page for that token's contract (or issuing account) and that the value is within 1% of what it shows now, after decimals. For backing rows, check the component, amount and as-of date against the report, and that "held_at" is what the report says about who holds it. Entity rows (kind "entity") check every clause of the wrapper label and note. Trackers never support a row. Be strict and literal; do not fix anything. Write `/tmp/verification-<today>-<n>.json` as {"checked_at": "<today>", "checker": "independent agent", "results": [{"row", "source_url", "verdict", "note"}]}, one entry per row, leave no helper files in the repo, and reply with counts and one line per finding.

4. `python3 tokenization/tools/merge_verify.py /tmp/verification-<today>-<n>.json run-<today>`
   For collector readings, the checker recomputes the value from the raw snapshot (`git show origin/collect:...`) and checks the address against the issuer's page in `address_source`.
5. Fix each finding by cutting the row back to what its page says, or remove a new row and record it under `gaps`. Log every fix in `verification_addressed` ({date, rows, note}) and, for a row already published, in `corrections`. Rebuild, pack only the changed rows, and run another independent pass. Stop after three passes: anything still open stays in `verification_pending`, and the page shows it as unchecked.

## 6. Gate (flag only)

`python3 tokenization/tools/log_gate.py /tmp/live-ledger.json tokenization/ledger.json run-<today> <today>`. It prints PASS or FLAGGED with the reasons (either headline moves more than 5%, one token moves $5B or 20%, a token enters above $1B, a netting row changes, or a reconciliation fails) and logs any flags in `gate_log`. Publish either way.

If nothing changed since the last run (no reading added or replaced, no new or changed row, no correction, no verification result), do not commit or publish; finish with a one-line "no change" report.

## 7. Share card (optional)

`cd /tmp && npm i @fontsource/hanken-grotesk @fontsource/jetbrains-mono`, then `python3 tokenization/tools/og_card.py tokenization/ledger.json /tmp/node_modules/@fontsource tokenization/og.png`. Skip it, and say so, if Playwright or Chrome is missing.

## 8. Publish

1. **Site:** create branch `daily/<today>` from the latest `origin/main`, commit only `tokenization/` (a message listing what changed, plus the session's attribution lines), push, open a pull request through the REST API (`gh api repos/3nchiridion/buildout-ledger/pulls -X POST -f title=... -f head=daily/<today> -f base=main -F body=@<file>`; GraphQL is unavailable), and squash-merge it (`gh api repos/3nchiridion/buildout-ledger/pulls/<n>/merge -X PUT -f merge_method=squash`). If `main` moved, rebase onto it first; only `tokenization/` may differ. Then confirm the `pages build and deployment` run for the merge commit finished with success (`gh api "repos/3nchiridion/buildout-ledger/actions/runs?per_page=5"`).
2. **Artifact:** `get_artifact` on the slug for its current version and read mode, then `publish_files` in patch mode with `base_version` (and `shared_live` if the read mode is users, org or public): `ledger.json`, `raw/declared.json`, `raw/readings.csv` and `verification.json`, each from `tokenization/`. Add `index.html` only if it changed.

## 9. Report

A short message. First line: the two headlines, before and after (tokenized money; tokenized assets). Then, one line each: gate flags; new rows and players (ids); readings added or replaced; reports and filings read; pending closes resolved; verifier results and what is still unchecked; anything that could not be read or sourced from primary material; and any step not completed, with why. Do not publish a ledger that failed validation.
