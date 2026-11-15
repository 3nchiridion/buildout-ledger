#!/usr/bin/env python3
"""Renders the 1200x630 share card for buildoutledger.com/tokenization from the built ledger.
Usage: og_card.py LEDGER_JSON FONT_DIR OUT_PNG  (FONT_DIR: node_modules/@fontsource after `npm i @fontsource/hanken-grotesk @fontsource/jetbrains-mono`)"""
import json, sys, asyncio, os
from playwright.async_api import async_playwright
L = json.load(open(sys.argv[1])); FD = sys.argv[2]; OUT = sys.argv[3]
E = {e["id"]: e for e in L["entities"]}; H = L["headline"]
def money(v):
    return f"${v/1e12:.2f}T" if v >= 1e12 else f"${v/1e9:.0f}B" if v >= 1e11 else f"${v/1e9:.1f}B" if v >= 1e9 else f"${v/1e6:.0f}M"
by = sorted(((i, x) for i, x in H["by_instrument"].items() if E[i].get("asset_class") == "money" and x.get("counted", True) and x.get("ok", True)), key=lambda t: -t[1]["amount"])
money_ok = [(i, x["amount"]) for i, x in H["by_instrument"].items() if E[i].get("asset_class") == "money" and E[i].get("counted")]
money_ok.sort(key=lambda t: -t[1])
top = money_ok[:2]; other = H["money"] - sum(v for _, v in top); shown = H["shown_not_counted"]["money"]
segs = [("#16171B", top[0][1], f"{money(top[0][1])} {E[top[0][0]]['name']}"), ("#646872", top[1][1], f"{money(top[1][1])} {E[top[1][0]]['name']}"),
        ("#B9BDC5", other, f"{money(other)} other dollar tokens")]
asof = L.get("as_of") or L.get("asof") or "2026-11-14"
import datetime; d = datetime.date.fromisoformat(asof[:10]); asof_s = f"{d.day} {d.strftime('%b').upper()} {d.year}"
total = sum(s[1] for s in segs) + shown
bar = "".join(f'<i style="flex:{v/total};background:{c}"></i>' for c, v, _ in segs) + f'<i class="press" style="flex:{shown/total}"></i>'
key = "".join(f'<span><b style="background:{c}"></b>{t}</span>' for c, _, t in segs)
ROLES = [("ISSUES", "--t-instruments", ["Tether", "Circle", "Paxos", "Ondo", "BlackRock"]),
         ("DISTRIBUTES", "--t-distribution", ["Coinbase", "Binance", "Kraken", "Robinhood"]),
         ("TOKENIZES", "--t-issuance", ["Securitize", "Superstate", "Galaxy"]),
         ("RUNS A LEDGER", "--t-ledgers", ["Arc", "Robinhood Chain", "Base", "Canton"]),
         ("KEEPS RESERVES", "--t-reserves", ["Circle Reserve Fund", "BNY", "State Street"])]
roles = "".join(f'<div class="box"><div class="k">{k}</div><div class="chips">' + "".join(f'<span style="background:var({t})">{n}</span>' for n in ns) + "</div></div>" for k, t, ns in ROLES)
roles += '<div class="box reg"><div class="k">CHARTERS AND RULES</div><div class="chips">' + "".join(f"<span>{n}</span>" for n in ["OCC", "SEC", "NYDFS", "FCA", "HKMA"]) + "</div></div>"
ff = "".join(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('file://{FD}/{pkg}/files/{pkg}-latin-{w}-normal.woff2') format('woff2')}}"
             for fam, pkg, ws in (("Hanken Grotesk", "hanken-grotesk", (400, 500, 600, 700)), ("JetBrains Mono", "jetbrains-mono", (400, 500, 600))) for w in ws)
HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
:root{{--paper:#F6F5F1;--ink:#16171B;--ink-2:#3B3E46;--muted:#6C717D;--line:#DEDBD3;--line-2:#C8C4BA;--warn:#A86A12;
--t-distribution:#FBE7EE;--t-instruments:#E6EDFB;--t-issuance:#E2F2E9;--t-ledgers:#FCEEDC;--t-reserves:#F7F0D3;--t-capital:#EDEBE6;
--sans:'Hanken Grotesk',sans-serif;--mono:'JetBrains Mono',monospace}}
*{{box-sizing:border-box}} body{{margin:0;width:1200px;height:630px;background:var(--paper);color:var(--ink);font-family:var(--sans);position:relative;overflow:hidden}}
.l{{position:absolute;left:64px;top:58px;width:580px}}
.kick{{font:500 15px var(--mono);letter-spacing:.08em;color:var(--muted)}}
h1{{font:700 54px/1.02 var(--sans);letter-spacing:-.02em;margin:18px 0 16px}}
.sub{{font:400 20px/1.35 var(--sans);color:var(--ink-2);margin:0 0 26px}}
.n{{display:flex;align-items:flex-end;gap:16px}} .n b{{font:600 72px/0.9 var(--mono);letter-spacing:-.03em}} .n span{{font:400 17px/1.3 var(--sans);color:var(--ink-2);padding-bottom:4px}}
.bar{{display:flex;height:13px;border-radius:2px;overflow:hidden;margin:22px 0 10px}} .bar i{{display:block}}
.press{{background:repeating-linear-gradient(135deg,var(--warn) 0 3px,#F3E6D2 3px 7px)}}
.key{{display:flex;flex-wrap:wrap;gap:4px 18px;font:400 15px var(--sans);color:var(--ink-2)}} .key b{{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:7px;vertical-align:-1px}}
.key .p b{{background:repeating-linear-gradient(135deg,var(--warn) 0 2px,#F3E6D2 2px 5px)}}
.a{{margin-top:16px;font:400 16px var(--sans);color:var(--ink-2)}} .a b{{font:600 22px var(--mono);color:var(--ink);margin-right:8px}}
.r{{position:absolute;left:724px;top:52px;width:412px;display:flex;flex-direction:column;gap:9px}}
.box{{border:1.4px solid var(--ink);border-radius:10px;background:#fff;padding:9px 12px 10px}}
.box.reg{{border:1.4px dashed var(--line-2);background:transparent}}
.k{{font:600 11.5px var(--mono);letter-spacing:.06em;margin-bottom:7px}} .reg .k{{color:var(--muted)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}} .chips span{{font:500 14px var(--sans);border:1.2px solid var(--ink);border-radius:7px;padding:4px 10px;white-space:nowrap}}
.reg .chips span{{background:#fff;box-shadow:0 0 0 2px #fff,0 0 0 3px var(--ink)}}
.url{{position:absolute;right:64px;bottom:40px;font:500 17px var(--mono)}}
</style></head><body>
<div class="l"><div class="kick">AS OF {asof_s} · EVERY LINE IS A SOURCED ROW</div>
<h1>The Tokenization<br>Buildout Ledger</h1>
<p class="sub">What is outstanding on-chain, who issues it, where it settles and what backs it.</p>
<div class="n"><b>{money(H['money'])}</b><span>tokenized money: dollar tokens read from chain, attested or filed</span></div>
<div class="bar">{bar}</div>
<div class="key">{key}<span class="p"><b></b>{money(shown)} crypto-collateralised, not counted</span></div>
<div class="a"><b>{money(H['assets'])}</b>tokenized assets, never added to money</div></div>
<div class="r">{roles}</div><div class="url">buildoutledger.com/tokenization</div></body></html>"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1200, "height": 630})
        tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_og.html"); open(tmp, "w").write(HTML)
        await pg.goto("file://" + tmp); await pg.wait_for_timeout(800)
        await pg.screenshot(path=OUT); os.remove(tmp); await b.close()
asyncio.run(main()); print("wrote", OUT)
