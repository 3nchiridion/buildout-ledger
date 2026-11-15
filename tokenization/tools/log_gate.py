#!/usr/bin/env python3
"""Runs the gate against the live ledger and logs its flags in raw/declared.json 'gate_log'. The gate flags; it never holds.
Usage: python3 tokenization/tools/log_gate.py LIVE_LEDGER.json NEW_LEDGER.json RUN_ID DATE
Always exits 0 and prints PASS or FLAGGED with the reasons."""
import json, os, subprocess, sys
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
live, new, run, date = sys.argv[1:5]
p = subprocess.run([sys.executable, os.path.join(T, "harness.py.txt"), "--raw", os.path.join(T, "raw"), "gate", "--live", live, "--new", new], capture_output=True, text=True)
flags = [l.strip()[2:] for l in p.stdout.splitlines() if l.strip().startswith("- ")]
D = json.load(open(os.path.join(T, "raw", "declared.json")))
if flags:
    D.setdefault("gate_log", []).append({"run": run, "date": date, "flags": flags, "published": True, "note": "Flagged by the gate and published, per the gate rule."})
    json.dump(D, open(os.path.join(T, "raw", "declared.json"), "w"), indent=1, ensure_ascii=False)
print(("FLAGGED\n" + "\n".join(" - " + f for f in flags)) if flags else "PASS")
