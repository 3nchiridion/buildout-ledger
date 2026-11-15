#!/usr/bin/env python3
"""Merges one verifier pass into verification.json and clears confirmed rows from raw/declared.json 'verification_pending'.
A row that is not confirmed is added to the pending list, so the page shows it as unchecked until a later pass confirms it.
Usage: python3 tokenization/tools/merge_verify.py RESULTS.json RUN_ID
RESULTS.json: {"checked_at", "checker", "results": [{"row", "source_url", "verdict": confirmed|finding|unreadable, "note"}]}"""
import json, os, sys
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = json.load(open(sys.argv[1])); run = sys.argv[2]
V = json.load(open(os.path.join(T, "verification.json"))); D = json.load(open(os.path.join(T, "raw", "declared.json")))
n = V["counts"].get("passes", 0) + 1; conf, open_ = [], []
for r in R["results"]:
    if r["verdict"] == "confirmed": conf.append(r["row"])
    else:
        open_.append(r["row"])
        V["findings"].append({"row": r["row"], "severity": "unreadable" if r["verdict"] == "unreadable" else "finding", "pass": n, "run": run, "source_url": r.get("source_url"), "note": r.get("note")})
V["confirmed"] = sorted(set(V["confirmed"]) | set(conf)); V["rows_checked"] += len(R["results"]); V["verified_at"] = R.get("checked_at", V["verified_at"])
c = V["counts"]; c["confirmed"] = len(V["confirmed"]); c["findings"] = len(V["findings"]); c["rows_with_findings"] = len({f["row"] for f in V["findings"]}); c["passes"] = n
json.dump(V, open(os.path.join(T, "verification.json"), "w"), indent=1, ensure_ascii=False)
D["verification_pending"] = sorted((set(D.get("verification_pending", [])) - set(conf)) | set(open_))
json.dump(D, open(os.path.join(T, "raw", "declared.json"), "w"), indent=1, ensure_ascii=False)
print(f"pass {n}: {len(conf)} confirmed, {len(open_)} not confirmed {open_}; still pending: {D['verification_pending']}")
