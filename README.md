# The AI Buildout Ledger

An interactive map of who pays whom to build AI: **[buildoutledger.com](https://buildoutledger.com)**

Every line on the map is a sourced row in `ledger.json`. Each row carries its source, a grade, an as-of date and a definition of what the figure measures. The map draws nothing that isn't in the ledger.

## How to read it

- **Layers:** applications, models, infrastructure, chips and energy, with capital (investors, lenders, bonds, governments) outside the stack.
- **Colour is the type of money:** equity, purchase commitment, capital spending, debt.
- **The line's pattern is the status:** solid means cash moved, long dashes mean signed, short dashes mean announced, dots mean press reports only.
- **Grades:** `filed` (SEC filings), `announced` (the company's own statement), `reported` (press only; shown, never added to the headline), `estimate`.
- **Headline:** equity plus purchase commitments that filings or the companies themselves state. It is gross: money is counted again at each layer it passes through, and multi-year deals count in full.
- **Scope:** rows from July 2025 on. A tie is drawn when it is at least $1B or 200 MW, or when an AI lab or hyperscaler is a counterparty.

## How it updates

A scheduled agent run collects new filings and announcements each day and rebuilds the ledger with `harness.py`. A separate agent that hasn't seen the work checks every new or changed row against its source (`verification.json`). A gate holds any update that moves the headline more than 5%, or any single row by $50B or more, for review before it goes live. History is append-only: revisions and corrections are logged on the row they change.

## Files

| Path | What it is |
|---|---|
| `index.html` | The map (one self-contained page) |
| `ledger.json` | The built ledger the map draws |
| `raw/declared.json` | Every declared row with its source, revisions and corrections |
| `raw/xbrl_facts.csv` | SEC XBRL facts behind the filed figures |
| `verification.json` | Results of the independent source check |
| `harness.py.txt` | The build, validation and gate code |
| `edition/2026-11-14/` | The frozen edition cited in the launch article; never updated |

## Corrections

Spot a wrong row? [Open a correction](../../issues/new?template=correction.yml) with the row and a source that contradicts it. Fixes are logged on the row, never silently overwritten.
