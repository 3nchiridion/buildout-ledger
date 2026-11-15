#!/usr/bin/env python3
"""What to read today. For each (token, chain) the ledger tracks, prints its latest reading and whether a new read is due:
  onchain   -> every run (explorer API; same method and URL)
  announced -> when the latest is 3+ days old (issuer page or release; look for a newer one)
  attested  -> when the latest as-of is 30+ days old (look for the next month's or quarter's report)
  filed     -> when the latest as-of is 30+ days old (look for a newer filing in the SEC submissions index)
Usage: python3 tokenization/tools/watchlist.py [--today YYYY-MM-DD] [--all]"""
import csv, os, sys, datetime, json
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
today = datetime.date.fromisoformat(sys.argv[sys.argv.index("--today") + 1]) if "--today" in sys.argv else datetime.date.today()
rows = list(csv.DictReader(open(os.path.join(T, "raw", "readings.csv"))))
D = json.load(open(os.path.join(T, "raw", "declared.json")))
last = {}
for r in rows:
    k = (r["instrument"], r["chain"])
    if k not in last or r["as_of"] > last[k]["as_of"]: last[k] = r
AGE = {"onchain": 0, "announced": 3, "attested": 30, "filed": 30}
print(f"Watchlist for {today}: {len(last)} (token, chain) pairs\n")
for (inst, chain), r in sorted(last.items(), key=lambda kv: (AGE.get(kv[1]["grade"], 30), kv[0])):
    age = (today - datetime.date.fromisoformat(r["as_of"])).days
    due = age >= AGE.get(r["grade"], 30)
    if not due and "--all" not in sys.argv: continue
    print(f"[{'DUE' if due else 'ok '}] {inst}/{chain}  latest {r['as_of']} ({age}d)  {r['grade']} via {r['method']}")
    print(f"      {r['source_url']}")
    if r["note"]: print(f"      how it was read: {r['note'][:300]}")
print("\nAlso check: entries in raw/declared.json 'watchlist' (SEC submissions indexes for fund filings), 'pending_close', and 'gaps'.")
for w in D.get("watchlist", []):
    print(f"  watchlist: {w['entity']}/{w['chain']}  {w['method']}  {w['url']}")
for p in D.get("pending_close", []):
    print(f"  pending close: {json.dumps(p)[:200]}")
