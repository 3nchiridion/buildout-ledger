#!/usr/bin/env python3
"""Turns one day of collector snapshots (the `collect` branch) into readings, through tools/add_reading.py, so every
reading keeps the month rule and the checks. Prints each add_reading call it makes; --dry-run prints and writes nothing.

Usage: python3 tokenization/tools/from_snapshots.py DATE [--only ID,ID] [--dry-run]
  DATE is the snapshot folder (the UTC day the collector ran; take the newest folder under snapshots/). Readings are dated
  in New York time. Needs `git fetch origin +refs/heads/collect:refs/remotes/origin/collect` first.

Rules per registry entry (tokenization/collect/registry.json, value_rule):
  usd_per_token                 value = supply x the stated dollars per token (dollar tokens and $1 funds)
  none (absent)                 value = token count; the note says the value per token was not read
  supply_x_multiplier_x_close   value = the priced total the snapshot computed; unpriced tokens are named in the note
Reads with no ledger chain (probes), failed reads, and USTB (valued by the daily run from Superstate's NAV) are skipped."""
import json, os, subprocess, sys, urllib.parse, datetime
from zoneinfo import ZoneInfo
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
day = sys.argv[1]; dry = "--dry-run" in sys.argv
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
reg = {e["id"]: e for e in json.load(open(os.path.join(T, "collect", "registry.json")))["reads"]}
D = json.load(open(os.path.join(T, "raw", "declared.json"))); ENT = {e["id"]: e for e in D["entities"]}
sha = subprocess.run(["git", "rev-parse", "--short", "origin/collect"], capture_output=True, text=True, check=True).stdout.strip()
def show(path): return subprocess.run(["git", "show", f"origin/collect:snapshots/{day}/{path}"], capture_output=True, text=True, check=True).stdout
summ = json.loads(show("summary.json"))
CH = {"ethereum": "Ethereum", "tron": "Tron", "xrpl": "the XRP Ledger", "arbitrum": "Arbitrum", "optimism": "OP Mainnet", "polygon": "Polygon PoS", "avalanche": "Avalanche C-Chain",
      "solana": "Solana", "aptos": "Aptos", "robinhoodchain": "Robinhood Chain"}
done = set()
for s in summ["reads"]:
    e = reg.get(s["id"])
    if not e or not s["ok"] or e["kind"] == "probe_get" or (only and s["id"] not in only): continue
    tok, ch = e["token"], e["chain"]
    if tok == "ustb" or tok not in ENT or ch not in ENT or (tok, ch) in done: continue
    r = json.loads(show(s["id"] + ".json")); p = r["parsed"]; rule = (e.get("value_rule") or {}).get("type"); at = p.get("at") or {}
    where = f"block {at['block']}" if "block" in at else f"slot {at['slot']}" if "slot" in at else f"ledger version {at['ledger_version']}" if at.get("ledger_version") else "the explorer's current figure"
    ev = f"Raw response kept in the collect branch (commit {sha}), snapshots/{day}/{s['id']}.json, fetched {r['fetched_at']}."
    rpcs = e.get("rpc") if isinstance(e.get("rpc"), list) else [e.get("rpc")]
    host = urllib.parse.urlparse(p.get("rpc_used") or rpcs[0] or e.get("url") or "").netloc
    if rule == "usd_per_token":
        val = p["supply"] * float(e["value_rule"]["usd"]); basis = "total supply"
        note = f"{p['supply_text']} tokens at {where}, valued at ${e['value_rule']['usd']} a token. {ev}"
    elif rule == "supply_x_multiplier_x_close":
        val = p["value_usd_priced"]; basis = "supply x issuer multiplier x last close"
        dates = sorted({t['close_date'] for t in p['tokens'] if t.get('close_date')})
        note = (f"{p['priced']} of {p['tokens_listed']} active tokens in the issuer's registry priced: supply read at {where}, times the multiplier in the issuer's registry, "
                f"times the underlying's last daily close published by Cboe's delayed-quote service (close dates {dates[0]} to {dates[-1]}). "
                f"Not priced (no Cboe close found): {', '.join(p['unpriced']) or 'none'}. {ev}")
    else:
        val = p["supply"]; basis = "total supply (token count)"
        note = f"{p['supply_text']} tokens at {where}. A token count; the value per token was not read. {ev}"
    kind = e["kind"]
    method = ("Blockscout API" if kind == "blockscout_v2" else "Tronscan API" if kind == "tronscan_trc20" else "XRPSCAN API" if kind == "xrpscan_obligations"
              else f"Public RPC ({host}), read by the collector")
    src_url = e.get("url") if kind in ("blockscout_v2", "tronscan_trc20", "xrpscan_obligations") else e["explorer_url"]
    title = f"{'Blockscout' if kind == 'blockscout_v2' else 'Tronscan API' if kind == 'tronscan_trc20' else 'XRPSCAN API' if kind == 'xrpscan_obligations' else 'Explorer page'}, {CH.get(ch, ch)}: {ENT[tok]['name']} contract"
    asof = datetime.datetime.fromisoformat(r["fetched_at"]).astimezone(ZoneInfo("America/New_York")).date().isoformat()   # the ledger dates readings in New York time
    cmd = [sys.executable, os.path.join(T, "tools", "add_reading.py"), "--instrument", tok, "--chain", ch, "--as-of", asof, "--available", asof, "--value", f"{val:.2f}",
           "--basis", basis, "--grade", "onchain", "--method", method, "--source-title", title, "--source-url", src_url, "--note", note]
    print(" ".join(repr(c) if " " in c else c for c in cmd[1:3]), tok, ch, f"${val:,.2f}")
    if not dry:
        out = subprocess.run(cmd, capture_output=True, text=True); print("   ", (out.stdout or out.stderr).strip())
        if e.get("also_total"):   # the token lives on this chain only, so the chain read is also its total
            t = list(cmd); t[t.index("--chain") + 1] = "all"
            out = subprocess.run(t, capture_output=True, text=True); print("    total:", (out.stdout or out.stderr).strip())
    done.add((tok, ch))
