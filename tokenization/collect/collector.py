#!/usr/bin/env python3
"""The Tokenization Buildout Ledger's collector. Runs in GitHub Actions (open network, keyless), never in the ledger build.
Reads every entry in registry.json, keeps each raw response word for word with its URL, request and time, and parses the
figure it carries. It never writes ledger rows: the daily run turns snapshots into readings, and the verifier recomputes
every number from the saved responses.

Usage: python3 collector.py REGISTRY.json OUT_DIR
Writes OUT_DIR/<date>/<id>.json for each read, OUT_DIR/<date>/summary.json, and OUT_DIR/<date>/log.txt.
Standard library only."""
import json, os, sys, time, datetime, hashlib, urllib.request, urllib.error

UA = "buildoutledger-collector/1.0 (+https://buildoutledger.com/tokenization)"
TIMEOUT = 40


def http(url, body=None, headers=None, tries=3, backoff=2):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for k in range(tries):
        req = urllib.request.Request(url, data=data, headers=h, method="POST" if data is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return {"status": r.status, "headers": {x: r.headers.get(x) for x in ("Date", "Content-Type", "X-Aptos-Ledger-Version", "X-Aptos-Block-Height") if r.headers.get(x)},
                        "text": r.read().decode("utf-8", "replace")}
        except urllib.error.HTTPError as e:
            last = {"status": e.code, "headers": {}, "text": e.read().decode("utf-8", "replace")[:4000]}
            if e.code not in (429, 500, 502, 503, 504):
                return last
        except Exception as e:  # network error: retry
            last = {"status": None, "headers": {}, "text": f"{type(e).__name__}: {e}"}
        time.sleep(backoff * (k + 1))
    return last


def rpc(url, method, params):
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}


def units(raw, dec):
    """Exact decimal string of raw / 10**dec, then float for convenience."""
    raw = int(raw); dec = int(dec)
    s = str(abs(raw)).rjust(dec + 1, "0")
    txt = ("-" if raw < 0 else "") + (s[:-dec] + "." + s[-dec:] if dec else s)
    return txt, float(txt)


def read(e, calls):
    """Fills calls (list of {request, response}) and returns parsed: raw_supply, decimals, supply, at."""
    k = e["kind"]; p = {}

    def call(url, body=None, headers=None):
        r = http(url, body, headers); calls.append({"request": {"url": url, "method": "POST" if body is not None else "GET", "body": body}, "response": r}); return r

    if k == "blockscout_v2":
        r = call(e["url"]); j = json.loads(r["text"])
        p["raw_supply"], p["decimals"] = j["total_supply"], j["decimals"]
        p["holders"] = j.get("holders_count") or j.get("holders")
    elif k == "tronscan_trc20":
        r = call(e["url"]); j = json.loads(r["text"]); t = j["trc20_tokens"][0]
        p["raw_supply"], p["decimals"] = t.get("total_supply_with_decimals") or t["total_supply"], t["decimals"]
    elif k == "xrpscan_obligations":
        r = call(e["url"]); j = json.loads(r["text"])
        rows = j if isinstance(j, list) else j.get("obligations", [])
        row = rows[0] if len(rows) == 1 else next(x for x in rows if x.get("currency") in (e["currency"], e.get("currency_hex")))
        p["supply_text"] = str(row["value"]); p["supply"] = float(row["value"])
    elif k == "evm_rpc":
        urls = e["rpc"] if isinstance(e["rpc"], list) else [e["rpc"]]
        for u in urls:
            bn = call(u, rpc(u, "eth_blockNumber", []))
            try:
                block = json.loads(bn["text"])["result"]; break
            except Exception:
                continue
        else:
            raise RuntimeError("no RPC answered: " + ", ".join(urls))
        ts = call(u, rpc(u, "eth_call", [{"to": e["address"], "data": "0x18160ddd"}, block]))
        dc = call(u, rpc(u, "eth_call", [{"to": e["address"], "data": "0x313ce567"}, block]))
        p["rpc_used"] = u
        p["raw_supply"] = int(json.loads(ts["text"])["result"], 16); p["decimals"] = int(json.loads(dc["text"])["result"], 16)
        p["at"] = {"block": int(block, 16)}
    elif k == "solana_spl":
        r = call(e["rpc"], rpc(e["rpc"], "getTokenSupply", [e["address"], {"commitment": "finalized"}]))
        j = json.loads(r["text"])["result"]
        p["raw_supply"], p["decimals"] = j["value"]["amount"], j["value"]["decimals"]; p["at"] = {"slot": j["context"]["slot"]}
    elif k == "aptos_fa":
        base = e["rpc"].rstrip("/"); meta = e["address"]
        if e.get("metadata_view"):   # the published address is a package; its view function names the token's metadata object
            m = call(base + "/view", {"function": e["metadata_view"], "type_arguments": [], "arguments": []})
            mv = json.loads(m["text"])[0]; meta = mv["inner"] if isinstance(mv, dict) else mv
            p["metadata_object"] = meta
        s = call(base + "/view", {"function": "0x1::fungible_asset::supply", "type_arguments": ["0x1::fungible_asset::Metadata"], "arguments": [meta]})
        d = call(base + "/view", {"function": "0x1::fungible_asset::decimals", "type_arguments": ["0x1::fungible_asset::Metadata"], "arguments": [meta]})
        sv = json.loads(s["text"])[0]; sv = sv["vec"][0] if isinstance(sv, dict) else sv
        p["raw_supply"], p["decimals"] = sv, json.loads(d["text"])[0]
        p["at"] = {"ledger_version": s["headers"].get("X-Aptos-Ledger-Version")}
    elif k == "robinhood_rhj":
        # Robinhood's own Stock Token registry (issuer RHJ), then each token's supply on Robinhood Chain at one pinned block,
        # then the underlying's last daily close from Cboe's delayed-quote service. Value = supply x issuer multiplier x close.
        reg = call(e["registry"]); A = [a for a in json.loads(reg["text"])["assets"] if a.get("status") == "ASSET_STATUS_ACTIVE"]
        urls = e["rpc"] if isinstance(e["rpc"], list) else [e["rpc"]]
        for u in urls:
            bn = call(u, rpc(u, "eth_blockNumber", []))
            try:
                block = json.loads(bn["text"])["result"]; break
            except Exception:
                continue
        else:
            raise RuntimeError("no RPC answered")
        toks = [(a, d["contractAddress"]) for a in A for d in a["deployments"] if d["chainId"] == e["chain_id"]]
        sup = {}
        for i in range(0, len(toks), 20):
            batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_call", "params": [{"to": addr, "data": "0x18160ddd"}, block]} for j, (_, addr) in enumerate(toks[i:i + 20], start=i)]
            r = call(u, batch)
            for x in json.loads(r["text"]):
                if "result" in x: sup[x["id"]] = int(x["result"], 16)
            time.sleep(0.5)
        rows, total, priced, unpriced = [], 0.0, 0, []
        for j, (a, addr) in enumerate(toks):
            sym = a["tokenSymbol"]; dec = int(a.get("tokenDecimals", 18)); m = float(a.get("currentMultiplier") or 1)
            raw = sup.get(j); row = {"symbol": sym, "name": a["tokenName"], "isin": a.get("isin"), "address": addr, "raw_supply": str(raw) if raw is not None else None,
                                     "decimals": dec, "multiplier": a.get("currentMultiplier")}
            if raw is not None:
                row["supply_text"], row["supply"] = units(raw, dec)
                q = http(e["price_url"].format(sym=sym.replace(".", "/")), tries=6, backoff=10)
                row["price_request"] = e["price_url"].format(sym=sym.replace(".", "/")); row["price_status"] = q["status"]
                try:
                    h = json.loads(q["text"]); last = h["data"][-1]
                    row["price_sha256"] = hashlib.sha256(q["text"].encode()).hexdigest(); row["price_bytes"] = len(q["text"]); row["price_generated"] = h.get("timestamp")
                    row["price_tail"] = h["data"][-3:]; row["close_date"], row["close"] = last["date"], float(last["close"])
                    row["value_usd"] = round(row["supply"] * m * row["close"], 2); total += row["value_usd"]; priced += 1
                except Exception as ex:
                    row["price_error"] = f"{type(ex).__name__}: {str(q['text'])[:200]}"; unpriced.append(sym)
                time.sleep(1.0)
            rows.append(row)
        p.update({"at": {"block": int(block, 16)}, "rpc_used": u, "tokens": rows, "tokens_listed": len(toks), "priced": priced, "unpriced": unpriced,
                  "value_usd_priced": round(total, 2)})
        p["supply_text"] = f"{priced} of {len(toks)} tokens priced, ${total:,.2f}"
        return p
    elif k == "probe_get":   # keep a raw GET response for inspection; parses nothing
        for u in e["urls"]:
            call(u)
        return p
    else:
        raise ValueError("unknown kind " + k)
    if "raw_supply" in p:
        p["supply_text"], p["supply"] = units(p["raw_supply"], p["decimals"])
        p["raw_supply"] = str(p["raw_supply"])
    return p


def main():
    reg = json.load(open(sys.argv[1])); out = sys.argv[2]
    now = datetime.datetime.now(datetime.timezone.utc); day = now.strftime("%Y-%m-%d")
    d = os.path.join(out, day); os.makedirs(d, exist_ok=True)
    log, summary = [], []
    for e in reg["reads"]:
        if e.get("disabled"):
            continue
        t0 = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        rec = {"id": e["id"], "token": e["token"], "chain": e["chain"], "kind": e["kind"], "address": e.get("address"), "fetched_at": t0,
               "explorer_url": e.get("explorer_url"), "address_source": e.get("address_source"), "value_rule": e.get("value_rule")}
        calls = []
        try:
            p = read(e, calls)
            rec.update({"calls": calls, "parsed": p, "ok": True})
            rule = e.get("value_rule") or {}
            if rule.get("type") == "usd_per_token":
                rec["value_usd"] = round(p["supply"] * float(rule["usd"]), 2)
            log.append(f"{t0} OK   {e['id']}: {p.get('supply_text')}")
        except Exception as ex:
            rec.update({"calls": calls, "ok": False, "error": f"{type(ex).__name__}: {ex}"})
            log.append(f"{t0} FAIL {e['id']}: {type(ex).__name__}: {ex}")
        json.dump(rec, open(os.path.join(d, e["id"] + ".json"), "w"), indent=1, ensure_ascii=False)
        summary.append({k: rec.get(k) for k in ("id", "token", "chain", "ok", "fetched_at", "value_usd", "error")} | {"supply_text": (rec.get("parsed") or {}).get("supply_text"), "at": (rec.get("parsed") or {}).get("at")})
        time.sleep(0.4)
    json.dump({"date": day, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "reads": summary}, open(os.path.join(d, "summary.json"), "w"), indent=1)
    open(os.path.join(d, "log.txt"), "w").write("\n".join(log) + "\n")
    print("\n".join(log))
    print(f"{sum(1 for s in summary if s['ok'])} of {len(summary)} reads OK")


if __name__ == "__main__":
    main()
