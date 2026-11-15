#!/usr/bin/env python3
"""Adds one balance reading to raw/readings.csv, checked, and applies the history rule:
month-end balances plus the latest reading. Within a calendar month, a new on-chain reading REPLACES the previous
same-month on-chain reading for that (token, chain) unless the value moved 10% or more; the last reading of a month
stays as that month's close. Every other grade (attested, filed, announced) is always appended.

Usage:
  python3 tokenization/tools/add_reading.py --instrument usdt --chain ethereum --as-of 2026-11-15 --available 2026-11-15 \
      --value 95123456789 --basis "total supply" --grade onchain --method "Blockscout API" \
      --source-title "Blockscout, Ethereum: USDT contract" --source-url https://... --note "..."
Prints what it did. Exits non-zero, writing nothing, on any problem."""
import argparse, csv, json, os, sys, datetime
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(T, "raw", "readings.csv")
ap = argparse.ArgumentParser()
for a in ("instrument", "chain", "as-of", "available", "value", "basis", "grade", "method", "source-title", "source-url"):
    ap.add_argument("--" + a, required=True)
ap.add_argument("--note", default="")
a = ap.parse_args()
D = json.load(open(os.path.join(T, "raw", "declared.json")))
E = {e["id"]: e for e in D["entities"]}
def die(m): sys.exit("NOT ADDED: " + m)
if a.instrument not in E or E[a.instrument]["kind"] != "product": die(f"{a.instrument} is not a token on the ledger")
if a.chain not in ("all", "other") and (a.chain not in E or E[a.chain]["kind"] != "ledger"): die(f"{a.chain} is not a chain on the ledger (add it as a ledger entity first)")
if a.grade not in ("onchain", "attested", "filed", "announced"): die("grade must be onchain, attested, filed or announced")
for d in (a.as_of, a.available):
    try: datetime.date.fromisoformat(d)
    except ValueError: die(f"bad date {d}")
if a.available < a.as_of: die("available is before as_of")
try: v = float(a.value); assert v >= 0
except Exception: die("value must be a non-negative number in USD")
if not a.source_url.startswith("http"): die("source_url must be a URL")
rows = list(csv.DictReader(open(P))); cols = list(rows[0].keys())
if any(r["instrument"] == a.instrument and r["chain"] == a.chain and r["as_of"] == a.as_of and r["grade"] == a.grade for r in rows):
    die(f"a {a.grade} reading for {a.instrument}/{a.chain} on {a.as_of} already exists")
new = {"instrument": a.instrument, "chain": a.chain, "as_of": a.as_of, "available": a.available, "value": str(int(round(v))), "basis": a.basis,
       "grade": a.grade, "method": a.method, "source_title": a.source_title, "source_url": a.source_url, "note": a.note}
action, replace_at = "appended", None
if a.grade == "onchain":
    prev = [i for i, r in enumerate(rows) if r["instrument"] == a.instrument and r["chain"] == a.chain and r["grade"] == "onchain"]
    if prev:
        i = max(prev, key=lambda j: rows[j]["as_of"]); p = rows[i]; pv = float(p["value"])
        if p["as_of"] > a.as_of: die(f"an on-chain reading dated {p['as_of']} is newer than {a.as_of}")
        moved = abs(v - pv) / pv if pv else 1.0
        if p["as_of"][:7] == a.as_of[:7]:
            if moved < 0.10: replace_at, action = i, f"replaced the same-month reading of {p['as_of']} (moved {moved:.2%})"
            else: action = f"appended; moved {moved:.1%} since {p['as_of']}, so both are kept"
if replace_at is None: rows.append(new)
else: rows[replace_at] = new
with open(P, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"{a.instrument}/{a.chain} {a.as_of} {a.grade} ${v:,.0f}: {action}. Observation id: o-{a.instrument}-{a.chain}-{a.as_of}")
