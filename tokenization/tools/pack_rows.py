#!/usr/bin/env python3
"""Packs rows for the independent verifier, grouped by source page, with every claim the row makes (amounts included).
Usage: python3 tokenization/tools/pack_rows.py OUT.json [--pending] [ID ...]
  --pending adds every id in raw/declared.json 'verification_pending'. An id 'ent-<entity>' packs that token's
  wrapper label and note, checked against the source of its 'issues' tie."""
import json, os, sys, collections
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
out = sys.argv[1]; ids = [x for x in sys.argv[2:] if not x.startswith("--")]
D = json.load(open(os.path.join(T, "raw", "declared.json")))
if "--pending" in sys.argv: ids += D.get("verification_pending", [])
ids = list(dict.fromkeys(ids))
L = json.load(open(os.path.join(T, "ledger.json"))); E = {e["id"]: e for e in L["entities"]}
idx = {}
for f in L["flows"]: idx[f["id"]] = ("flow", f)
for o in L.get("observations", []): idx[o["id"]] = ("observation", o)
for e in L["events"]: idx[e["id"]] = ("event", e)
for b in L.get("backing", []): idx[b["id"]] = ("backing", b)
for m in L.get("metrics", []): idx[m["id"]] = ("metric", m)
G = collections.OrderedDict(); missing = []
def add(url, row): G.setdefault(url, []).append(row)
nm = lambda i: E[i]["name"] if i in E else i
for i in ids:
    if i.startswith("ent-") and i[4:] in E:
        e = E[i[4:]]; tie = next((f for f in L["flows"] if f["type"] == "issues" and f["payee"] == e["id"]), None)
        if not tie: missing.append(i); continue
        add(tie["source_url"], {"row": i, "kind": "entity", "claim": f"Wrapper label: {(e.get('wrapper') or {}).get('label')}. Note: {e.get('note')}"}); continue
    if i not in idx: missing.append(i); continue
    k, r = idx[i]
    if k == "flow":
        row = {"row": i, "kind": k, "claim": f"{nm(r['payer'])} -> {nm(r['payee'])} ({r['type']}, status {r.get('status')}): {r.get('title')}", "label": r.get("label"),
               "amount_usd": r.get("amount_usd"), "amount_qualifier": r.get("amount_qualifier"), "date": r.get("date") or r.get("as_of"), "grade": r["grade"],
               "definition": r.get("definition"), "qualifier": r.get("qualifier")}
    elif k == "observation":
        row = {"row": i, "kind": k, "token": nm(r["subject"]), "chain": r.get("chain"), "amount_usd": r.get("value_usd"), "as_of": r.get("as_of"),
               "available": r.get("available"), "grade": r["grade"], "method": r.get("method"), "definition": r.get("definition")}
    elif k == "event":
        row = {"row": i, "kind": k, "date": r["date"], "claim": r["title"], "detail": r.get("detail"), "grade": r["grade"]}
    elif k == "backing":
        row = {"row": i, "kind": k, "token": nm(r["token"]), "component": r["component"], "held_at (where the reserve is held)": r.get("held_label"),
               "amount_usd": r["amount_usd"], "as_of": r["as_of"], "grade": r["grade"]}
    else:
        row = {"row": i, "kind": k, "entity": nm(r.get("entity")), "metric": r.get("metric"), "value": r.get("value"), "as_of": r.get("as_of"),
               "grade": r["grade"], "definition": r.get("definition")}
    add(r["source_url"], row)
json.dump([{"source_url": u, "rows": rs} for u, rs in G.items()], open(out, "w"), indent=1, ensure_ascii=False)
print(f"packed {sum(len(r) for r in G.values())} rows from {len(G)} sources into {out}" + (f"; not found: {missing}" if missing else ""))
