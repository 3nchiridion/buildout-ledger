# The Buildout Ledger

Interactive maps of who is building what, where every line is a sourced row. Free, no ads.

| Map | Address | Folder |
|---|---|---|
| The AI Buildout Ledger | [buildoutledger.com](https://buildoutledger.com) | repo root |
| The Tokenization Buildout Ledger | [buildoutledger.com/tokenization](https://buildoutledger.com/tokenization/) | `tokenization/` |

## The AI Buildout Ledger

An interactive map of who pays whom to build AI: **[buildoutledger.com](https://buildoutledger.com)**

Every line on the map is a sourced row in `ledger.json`. Each row carries its source, a grade, an as-of date and a definition of what the figure measures. The map draws nothing that isn't in the ledger.

### How to read it

- **Layers:** applications, models, infrastructure, chips and energy, with capital (investors, lenders, bonds, governments) outside the stack.
- **Colour is the type of money:** equity, purchase commitment, capital spending, debt.
- **The line's pattern is the status:** solid means cash moved, long dashes mean signed, short dashes mean announced, dots mean press reports only.
- **Grades:** `filed` (SEC filings), `announced` (the company's own statement), `reported` (press only; shown, never added to the headline), `estimate`.
- **Headline:** equity plus purchase commitments that filings or the companies themselves state. It is gross: money is counted again at each layer it passes through, and multi-year deals count in full.
- **Scope:** rows from July 2025 on. A tie is drawn when it is at least $1B or 200 MW, or when an AI lab or hyperscaler is a counterparty.

### How it updates

A scheduled agent run collects new filings and announcements each day and rebuilds the ledger with `harness.py`. A separate agent that hasn't seen the work checks every new or changed row against its source (`verification.json`). A gate holds any update that moves the headline more than 5%, or any single row by $50B or more, for review before it goes live. History is append-only: revisions and corrections are logged on the row they change.

### Files

| Path | What it is |
|---|---|
| `index.html` | The map (one self-contained page) |
| `ledger.json` | The built ledger the map draws |
| `raw/declared.json` | Every declared row with its source, revisions and corrections |
| `raw/xbrl_facts.csv` | SEC XBRL facts behind the filed figures |
| `verification.json` | Results of the independent source check |
| `harness.py.txt` | The build, validation and gate code |
| `edition/2026-11-14/` | The frozen edition cited in the launch article; never updated |

## The Tokenization Buildout Ledger

What is outstanding on-chain, who issues it, where it settles and what backs it: **[buildoutledger.com/tokenization](https://buildoutledger.com/tokenization/)**

### How to read it

- **Balance sheet (main view), left to right:** where reserves are held, what backs the token, the token, and the chains it is on. Ribbons carry dollars. Grey is a reserve whose holder is not named or a backing that is not published. A token held as backing by another token appears twice, joined by a dotted line.
- **Roles:** players down the side; issues, distributes, tokenizes, runs a ledger, keeps reserves, charter and deals across the top.
- **Time:** counted dollar tokens over time, with rules, charters and deals marked.
- **Headline:** two numbers, never added together. *Tokenized money* counts dollar tokens read from chain, attested by an accountant or filed. *Tokenized assets* counts funds, notes, gold and stocks on the same grades plus totals stated by the issuer, which are shown separately as issuer-stated. Where counted tokens hold each other, the overlap is netted out. Crypto-collateralised dollars (USDe, USDS) are shown and not counted.
- **Grades:** `onchain` (a public explorer read), `attested` (an accountant's report), `filed` (a regulator or SEC filing), `announced` (the company's own page or release), `reported` (press only; never counted), `estimate`.
- **Legal wrapper:** each token's tint is its legal form: national trust bank, other regulator, registered fund, private fund or note, bank deposit, crypto-collateralised, or no charter on the ledger.
- **Scope:** rows from January 2025. Money tokens from $1B outstanding, assets from $250M. Regulators for the US, EU, UK, Hong Kong, Singapore and the UAE. Trackers (rwa.xyz and the like) are used to find rows and are never a source for one.

### How it updates

Every reading comes from a keyless public source: an explorer API, an issuer's page or report, a regulator's site or an SEC filing index. The ledger is rebuilt with `harness.py`, the same harness as the AI map with a profile per ledger; the AI ledger rebuilds byte-identically from it. A separate agent that hasn't seen the work checks every new or changed row against its source (`verification.json`). A gate flags any update that moves either headline more than 5%, moves one token by $5B or 20%, brings in a token above $1B, changes a netting row or fails a reconciliation; flagged updates are published and the flags are logged in `raw/declared.json` (`gate_log`). History is append-only: corrections are logged on the rows they change.

### Files

| Path | What it is |
|---|---|
| `tokenization/index.html` | The map (one self-contained page) |
| `tokenization/ledger.json` | The built ledger the map draws |
| `tokenization/raw/declared.json` | Every declared row with its source, backing, gaps, corrections, verification log and gate log |
| `tokenization/raw/readings.csv` | Every balance reading: chain reads, attestations, filings and issuer statements |
| `tokenization/verification.json` | Results of the independent source checks |
| `tokenization/harness.py.txt` | The build, validation and gate code (shared with the AI map) |
| `tokenization/page_patch.py.txt`, `tokenization/bs_view.js.txt` | How the page is derived from the AI map's page, and the balance sheet, role and time views |

## Corrections

Spot a wrong row on either map? [Open a correction](../../issues/new?template=correction.yml) with the row and a source that contradicts it. Fixes are logged on the row, never silently overwritten.
