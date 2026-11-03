#!/usr/bin/env python3
"""Builds the English and Hindi Gold Thermometer pages from gold/data/latest.json.

Writes build/gold-thermometer-en.html and build/gold-thermometer-hi.html. Everything, including
the gauge and the chart, is plain HTML and SVG, so search engines read the full page.
"""
import html
import json
import math
from urllib.parse import quote
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "build"
from texts import T, URL_EN, URL_HI
SITE = "https://9amtraders.com"
DEMO = "https://wa.me/919315906004?text=Hi%2C%20I%20want%20to%20book%20a%20free%20demo%20class"
COLORS = {"cheap": "#1f8a52", "fair": "#c9a227", "expensive": "#e07b28", "very_expensive": "#c1272d"}
ZONES = [("cheap", 0, 25), ("fair", 25, 60), ("expensive", 60, 85), ("very_expensive", 85, 100)]
SRC = {
    "gp": '<a href="https://goldprice.dev/" target="_blank" rel="noopener">goldprice.dev</a>',
    "fx": '<a href="https://frankfurter.dev/" target="_blank" rel="noopener">Frankfurter</a>',
    "wb": '<a href="https://www.worldbank.org/en/research/commodity-markets" target="_blank" rel="noopener">World Bank Commodity Price Data (The Pink Sheet)</a>',
}

CSS = """<style>
#n9gt{--navy:#14275a;--navy2:#0c1a3f;--red:#c1272d;--ink:#0e1a36;--grey:#5d6577;--line:#e3e7ef;--bg:#f5f7fb;
font-family:inherit;color:var(--ink);line-height:1.65;max-width:1080px;margin:0 auto;padding:0 16px;box-sizing:border-box}
#n9gt *{box-sizing:border-box}#n9gt a{color:var(--navy)}
#n9gt .hero{background:linear-gradient(160deg,#14275a,#0a1534);color:#fff;border-radius:18px;padding:34px 30px;margin:22px 0}
#n9gt .top{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
#n9gt .kicker{display:inline-block;background:var(--red);color:#fff;font-size:13px;font-weight:700;letter-spacing:1px;padding:5px 12px;border-radius:5px}
#n9gt .lang{color:#fff!important;font-weight:700;font-size:14px;text-decoration:none;border:1.5px solid rgba(255,255,255,.4);padding:5px 12px;border-radius:20px}
#n9gt h1{font-size:clamp(28px,4.6vw,42px);line-height:1.15;margin:14px 0 8px;color:#fff;font-weight:800}
#n9gt h1 span{color:#f2c94c}#n9gt .hero p{color:#d5ddf0;margin:0;max-width:760px}
#n9gt .reading{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;margin-bottom:16px}
#n9gt .gauge svg{width:100%;height:auto;display:block}
#n9gt .legend{display:flex;flex-wrap:wrap;gap:6px 12px;justify-content:center;font-size:13px;color:var(--grey);margin-top:4px}
#n9gt .legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}
#n9gt .lab{font-size:15px;color:var(--grey);margin:0}
#n9gt .big{font-size:clamp(34px,5vw,48px);font-weight:800;line-height:1.1;margin:2px 0 8px}
#n9gt .reading p{margin:0 0 8px}
#n9gt .cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:6px}
#n9gt .card{background:#fff;border:1px solid var(--line);border-top:4px solid var(--navy);border-radius:12px;padding:14px}
#n9gt .card h3{font-size:14px;color:var(--grey);margin:0 0 4px;font-weight:600}
#n9gt .card .v{font-size:24px;font-weight:800;color:var(--ink);line-height:1.2}
#n9gt .card p{font-size:13px;color:var(--grey);margin:6px 0 0;line-height:1.45}
#n9gt .attr{font-size:13px;color:var(--grey);margin:4px 0 18px}
#n9gt h2{font-size:clamp(22px,3.2vw,28px);margin:34px 0 8px;color:var(--navy);font-weight:800}
#n9gt h3{color:var(--navy)}
#n9gt .box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px}
#n9gt .note{font-size:14px;color:var(--grey);margin:8px 0 0}
#n9gt .chart svg{width:100%;height:auto;display:block}
#n9gt .sub{color:var(--grey);margin:0 0 12px}
#n9gt table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:15px}
#n9gt th,#n9gt td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left}
#n9gt th{background:var(--navy);color:#fff;font-size:14px}
#n9gt .dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:8px;vertical-align:middle}
#n9gt details{background:#fff;border:1px solid var(--line);border-radius:10px;padding:13px 17px;margin-bottom:10px}
#n9gt summary{font-weight:700;cursor:pointer;color:var(--navy)}#n9gt details p{margin:10px 0 0;color:var(--grey)}
#n9gt .cta{background:linear-gradient(160deg,#14275a,#0a1534);color:#fff;border-radius:18px;padding:28px;margin:34px 0 16px;text-align:center}
#n9gt .cta h2{color:#fff;margin:0 0 8px}#n9gt .cta p{color:#d5ddf0;margin:0 0 18px}
#n9gt .btn{display:inline-block;background:var(--red);color:#fff!important;text-decoration:none;font-weight:700;padding:14px 26px;border-radius:10px;box-shadow:0 5px 0 #7d1418}
#n9gt .disc{font-size:13px;color:var(--grey);border-top:1px solid var(--line);padding-top:12px;margin:14px 0}
#n9gt .stale{display:none;background:#fff5f5;border:1px solid #f3c7c9;border-left:5px solid var(--red);border-radius:10px;padding:12px 16px;margin:0 0 14px;font-size:15px}
#n9gt .needle{transform-origin:160px 160px;transform:rotate(var(--a))}
#n9gt .chg{font-size:13px;font-weight:700;margin:4px 0 0!important}#n9gt .chg.up{color:#1f8a52!important}#n9gt .chg.dn{color:#c1272d!important}
#n9gt .share{display:inline-flex;align-items:center;gap:8px;margin-top:6px;background:#25d366;color:#fff!important;text-decoration:none;font-weight:700;font-size:15px;padding:10px 16px;border-radius:9px}
#n9gt .share svg{width:20px;height:20px}
#n9gt .reading.pre .needle{transform:rotate(0deg)}
#n9gt .reading.pre .seg{stroke-dasharray:1;stroke-dashoffset:1}
#n9gt .reading.pre .bigname{opacity:0}
#n9gt .reading.go .seg{stroke-dasharray:1;animation:n9draw .55s ease-out var(--d) both}
#n9gt .reading.go .seg.on{animation:n9draw .55s ease-out var(--d) both,n9glow 1.2s ease-in-out 3.2s 3}
#n9gt .reading.go .needle{animation:n9sweep 2.6s ease-in-out .5s both}
#n9gt .reading.go .bigname{animation:n9up .5s ease-out 2.9s both}
@keyframes n9draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes n9sweep{0%{transform:rotate(0deg)}38%{transform:rotate(180deg)}74%{transform:rotate(calc(var(--a) + 6deg))}88%{transform:rotate(calc(var(--a) - 2deg))}100%{transform:rotate(var(--a))}}
@keyframes n9glow{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes n9up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){#n9gt .reading .seg,#n9gt .reading .needle,#n9gt .reading .bigname{animation:none!important}}
#n9gt .toc{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 6px}
#n9gt .toc a{font-size:14px;font-weight:600;text-decoration:none;color:var(--navy);background:#fff;border:1.5px solid var(--line);padding:6px 12px;border-radius:20px}
#n9gt section{scroll-margin-top:90px}
#n9gt .tw{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:12px}
#n9gt .tw table{min-width:520px}
#n9gt td.n,#n9gt th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
#n9gt .rate td:first-child{font-weight:700}#n9gt .rate tr.hl td{background:#fff8e1}
#n9gt .up{color:#1f8a52}#n9gt .dn{color:#c1272d}
#n9gt .calc{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:18px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px}
#n9gt .calc label{display:block;font-weight:700;color:var(--navy);font-size:14px;margin:0 0 4px}
#n9gt .calc input,#n9gt .calc select{width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:9px;font-size:16px;font-family:inherit;background:#fff;color:var(--ink)}
#n9gt .calc .f{margin-bottom:12px}#n9gt .calc .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#n9gt .calc .res{background:var(--bg);border-radius:12px;padding:14px 16px;align-self:start}
#n9gt .calc .res div{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px dashed #d6dbe6;font-variant-numeric:tabular-nums}
#n9gt .calc .res div:last-child{border:0}#n9gt .calc .res .tot{font-size:20px;font-weight:800;color:var(--navy)}
#n9gt .rel{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
#n9gt .rel a{display:block;background:#fff;border:1px solid var(--line);border-left:4px solid var(--red);border-radius:10px;padding:12px 14px;font-weight:700;text-decoration:none}
#n9gt .cards3{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:760px){#n9gt .calc{grid-template-columns:1fr}#n9gt .cards3{grid-template-columns:1fr}}
@media (max-width:560px){#n9gt .mh{display:none}#n9gt .tw table{min-width:0;font-size:14px}#n9gt th,#n9gt td{padding:9px 7px}#n9gt th.n{white-space:normal}}
@media (max-width:760px){#n9gt .reading{grid-template-columns:1fr}#n9gt .cards{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:420px){#n9gt .cards{grid-template-columns:1fr}#n9gt .hero{padding:26px 20px}}
</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def inr(n):
    """Indian digit grouping: 114170 -> 1,14,170."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + parts + [tail])


def pct(x, sign=True):
    return f"{x * 100:+.1f}%" if sign else f"{abs(x) * 100:.1f}%"


def month_name(t, m):
    y, mo = m.split("-")
    return f"{t['months'][int(mo) - 1]} {y}"


def day_name(t, d):
    y, mo, dd = d.split("-")
    return f"{int(dd)} {t['months'][int(mo) - 1]} {y}"


def gauge(L, t):
    """Semicircle gauge. The needle is drawn at 0 and rotated to the reading, so CSS can animate the swing.
    Without CSS or JavaScript the SVG transform still shows the final position."""
    cx, cy, r, w = 160, 160, 118, 26

    def pt(p, rad):
        a = math.pi * (1 - p / 100)
        return cx + rad * math.cos(a), cy - rad * math.sin(a)

    segs = ""
    for k, (name, a, b) in enumerate(ZONES):
        x1, y1 = pt(a, r)
        x2, y2 = pt(b, r)
        on = " on" if name == L["band"] else ""
        segs += (f'<path class="seg{on}" style="--d:{k * 0.12:.2f}s" pathLength="1" d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {x2:.1f},{y2:.1f}" '
                 f'fill="none" stroke="{COLORS[name]}" stroke-width="{w}"/>')
    for p_ in (25, 60, 85):
        xa, ya = pt(p_, r - w / 2 - 1)
        xb, yb = pt(p_, r + w / 2 + 1)
        segs += f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="#fff" stroke-width="3"/>'
    ticks = ""
    for p_ in range(0, 101, 10):
        xa, ya = pt(p_, r - w / 2 - 6)
        xb, yb = pt(p_, r - w / 2 - (12 if p_ % 50 == 0 else 9))
        ticks += f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="#b8c0d2" stroke-width="1.5"/>'
    deg = L["percentile"] * 1.8
    label = t["gauge_aria"].format(band=t["band"][L["band"]], pct=round(L["percentile"]))
    return (f'<svg viewBox="0 0 320 185" role="img" aria-label="{esc(label)}">{segs}{ticks}'
            f'<g class="needle" style="--a:{deg:.1f}deg" transform="rotate({deg:.1f} {cx} {cy})">'
            f'<path d="M{cx},{cy - 5} L{cx - (r - 34)},{cy} L{cx},{cy + 5} Z" fill="#0e1a36"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="12" fill="#0e1a36"/><circle cx="{cx}" cy="{cy}" r="4.5" fill="{COLORS[L["band"]]}"/>'
            f'<text x="28" y="180" font-size="13" fill="#5d6577">0</text><text x="282" y="180" font-size="13" fill="#5d6577">100</text></svg>')


def ribbon(L, t):
    """One coloured block per month for the last five years, coloured by that month's reading."""
    rb = L.get("ribbon") or []
    if not rb:
        return ""
    W, H, l, rgt, top, bh = 680, 70, 8, 8, 6, 34
    bw = (W - l - rgt) / len(rb)
    cells, years = "", ""
    for i, c in enumerate(rb):
        x = l + i * bw
        tip = f"{month_name(t, c['m'])}: {t['band'][c['band']]} ({round(c['pct'])}/100)"
        cells += (f'<rect x="{x:.1f}" y="{top}" width="{bw + 0.4:.1f}" height="{bh}" fill="{COLORS[c["band"]]}">'
                  f'<title>{esc(tip)}</title></rect>')
        if c["m"].endswith("-01"):
            years += (f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + bh + 6}" stroke="#fff" stroke-width="2"/>'
                      f'<text x="{x + 3:.1f}" y="{top + bh + 22}" font-size="12" fill="#5d6577">{c["m"][:4]}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(t["ribbon_h"])}">{cells}{years}</svg>'


def chart(L, t):
    pts = L["chart"]
    W, H, l, rgt, top, bot = 680, 300, 70, 16, 14, 34
    vals = [p["p"] for p in pts] + [p["a"] for p in pts] + [L["inr_10g_24k"]]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or 1000
    lo, hi = lo - pad, hi + pad
    n = len(pts)

    def X(i):
        return l + (W - l - rgt) * i / n

    def Y(v):
        return top + (H - top - bot) * (1 - (v - lo) / (hi - lo))

    grid = ""
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        y = Y(v)
        lab = f"₹{v / 100000:.2f}L" if hi >= 100000 else f"₹{v / 1000:.0f}k"
        grid += f'<line x1="{l}" x2="{W - rgt}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e7ef"/><text x="{l - 8}" y="{y + 4:.1f}" font-size="12" fill="#5d6577" text-anchor="end">{lab}</text>'
    for i, p in enumerate(pts):
        if p["m"].endswith("-01"):
            x = X(i)
            grid += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{H - bot}" stroke="#eef1f6"/><text x="{x:.1f}" y="{H - 12}" font-size="12" fill="#5d6577" text-anchor="middle">{p["m"][:4]}</text>'
    line = " ".join(f"{X(i):.1f},{Y(p['p']):.1f}" for i, p in enumerate(pts)) + f" {X(n):.1f},{Y(L['inr_10g_24k']):.1f}"
    avg = " ".join(f"{X(i):.1f},{Y(p['a']):.1f}" for i, p in enumerate(pts))
    tx, ty = X(n), Y(L["inr_10g_24k"])
    lg = t["legend"]
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(t["chart_h"])}">{grid}'
            f'<polyline points="{avg}" fill="none" stroke="#c1272d" stroke-width="2" stroke-dasharray="6 5"/>'
            f'<polyline points="{line}" fill="none" stroke="#14275a" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="6" fill="#c9a227" stroke="#fff" stroke-width="2"/></svg>'
            f'<div class="legend"><span><i style="background:#14275a"></i>{lg[0]}</span>'
            f'<span><i style="background:#c1272d"></i>{lg[1]}</span><span><i style="background:#c9a227"></i>{lg[2]}</span></div>')


def table(cols, rows, num_from=1, cls="", hide=()):
    """cols: header labels; rows: lists of cell HTML. Columns from num_from onwards are right-aligned numbers.
    Columns listed in hide are left out on small phone screens."""
    def k(i):
        return " ".join(x for x in ("n" if i >= num_from else "", "mh" if i in hide else "") if x)
    th = "".join(f'<th class="{k(i)}">{c}</th>' for i, c in enumerate(cols))
    body = ""
    for r in rows:
        trc = ""
        if isinstance(r, tuple):
            trc, r = r
        body += f'<tr class="{trc}">' + "".join(f'<td class="{k(i)}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def signed(x):
    return f'<span class="{"up" if x >= 0 else "dn"}">{pct(x)}</span>'


def page(L, lang):
    t = T[lang]
    band = L["band"]
    bname = t["band"][band]
    s = L["stretch"]
    x, d = pct(s, sign=False), t["above"] if s >= 0 else t["below"]
    p_ = round(L["percentile"])
    upd_d, upd_t = L["updated_ist"].split(" ")
    today = day_name(t, L["date"])
    india = {k: v for k, v in L["india_10g"].items()}
    g24, g22 = india["24"] / 10, india["22"] / 10
    url = SITE + (URL_EN if lang == "en" else URL_HI)

    # Today's rate table
    rate_rows = [(("hl" if k == "22" else ""), [t["karat"][k]] + [f"₹{inr(india[k] / 10 * w)}" for w in (1, 8, 10, 100)])
                 for k in ("24", "22", "18", "14")]
    yday = ""
    if L.get("prev"):
        diff = L["inr_10g_24k"] - L["prev"]["inr_10g"]
        diff_in = diff * (1 + L["duty"])
        chg = f'<b class="{"up" if diff >= 0 else "dn"}">{"+" if diff >= 0 else "−"}₹{inr(abs(diff_in))} ({pct(diff / L["prev"]["inr_10g"])})</b>'
        yday = f'<p class="note">{t["yday"].format(chg=chg, d=day_name(t, L["prev"]["date"]))}</p>'
    rate_note = t["rate_note"].format(usd=f'{L["usd_oz"]:,.2f}', fx=L["usdinr"], df=day_name(t, L["duty_from"]))

    # Thermometer
    pt_ = L["pattern"]
    if pt_["n"] >= 12:
        past = t["past"].format(band=bname, n=pt_["n"], up=round(pt_["up_share"] * 100),
                                med=pct(pt_["median"]), base=round(pt_["base_up_share"] * 100))
    else:
        past = t["past_few"].format(band=bname, n=pt_["n"])
    yoy = pct(L["yoy"]) if L.get("yoy") is not None else "–"
    share = "https://wa.me/?text=" + quote(t["share_t"].format(band=bname, pct=p_, p24=inr(india["24"]), url=url))
    legend = "".join(f'<span><i style="background:{COLORS[z]}"></i>{t["band"][z]}</span>' for z, _, _ in ZONES)
    zones = [[f'<span class="dot" style="background:{COLORS[z]}"></span><b>{t["band"][z]}</b>', t["zone_rule"][z]] for z, _, _ in ZONES]

    # Calculator, filled in for 10 g of 22K at 10% making charges and 3% GST
    r22 = india["22"]
    c_gold, c_make = r22, r22 * 0.10
    c_gst = (c_gold + c_make) * 0.03
    c_tot = c_gold + c_make + c_gst
    rates_json = json.dumps({k: india[k] for k in ("24", "22", "18", "14")})
    pur_opts = "".join(f'<option value="{k}"{" selected" if k == "22" else ""}>{t["karat"][k]}</option>' for k in ("24", "22", "18", "14"))
    co = t["c_out"]

    # Returns and the rupee's share
    yl = lambda n: (t["yr"] if n == 1 else t["yrs"]).format(n=n)
    ret_rows = [[yl(r["years"]), f'₹{inr(r["then"])}', f'₹{inr(L["inr_10g_24k"])}', signed(r["total"]), signed(r["cagr"])]
                for r in L.get("returns", [])]
    split_rows = [[yl(r["years"]), signed(r["usd"]), signed(r["inr"]), signed(r["total"]),
                   f'{round(r["rupee_share"] * 100)}%' if r["rupee_share"] is not None else "–"] for r in L.get("split", [])]
    s10 = next((r for r in L.get("split", []) if r["years"] == 10), None)
    s10v = round(s10["rupee_share"] * 100) if s10 and s10["rupee_share"] is not None else "–"
    r10 = next((r for r in L.get("returns", []) if r["years"] == 10), None)

    # History tables, newest first
    yrs = L.get("years", [])
    hist_rows = [[y["year"] + ("*" if y["months"] < 12 else ""), f'₹{inr(y["avg"])}', signed(y["change"]) if y["change"] is not None else "–",
                  f'₹{inr(y["low"])}', f'₹{inr(y["high"])}'] for y in reversed(yrs) if y["year"] >= "2001"]
    cur = yrs[-1] if yrs else {"year": "", "months": 0}
    m12_rows = [[month_name(t, m["m"]), f'₹{inr(m["p"])}', signed(m["chg"])] for m in reversed(L.get("last12", []))]
    d30 = L.get("daily30", [])
    d30_html = ""
    if len(d30) >= 2:
        d30_rows = [[day_name(t, x_["date"]), f'₹{inr(x_["india_24"])}', f'₹{inr(x_["inr_10g"])}'] for x_ in reversed(d30)]
        d30_html = f'<h3>{t["d30_h"]}</h3>' + table(t["d30_cols"], d30_rows)

    pur_rows = [list(r) for r in t["pur"]]
    unit_rows = [[lab, f'₹{inr(g24 * w)}', f'₹{inr(g22 * w)}'] for w, lab in t["units"]]
    ways_rows = [[f"<b>{a}</b>", b, c] for a, b, c in t["ways"]]

    faq_vals = dict(band=bname, x=x, dir=d, pct=p_, p24=inr(india["24"]), p22=inr(india["22"]),
                    r10=f'{r10["total"] * 100:.0f}%' if r10 else "–", c10=f'{r10["cagr"] * 100:.1f}%' if r10 else "–",
                    tola24=inr(g24 * 11.6638), tola22=inr(g22 * 11.6638))
    faqs = [(q, a.format(**faq_vals)) for q, a in t["faq"]]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
    ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
                     "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
                    ensure_ascii=False)
    toc = "".join(f'<a href="#n9gt-{i}">{lab}</a>' for i, lab in t["toc"])
    rel = "".join(f'<a href="{u}">{lab}</a>' for u, lab in t["rel"])

    return f"""<!-- 9AM Traders Academy | Gold price today and Gold Thermometer ({lang}). Built by gold/render.py in github.com/9amtraders/9am-ipo-data.
     Updated automatically every day. Edit the scripts, not this page. -->
<div id="n9gt" lang="{lang}" data-updated="{L['date']}">
{CSS}
<section class="hero">
  <div class="top"><span class="kicker">{t['updated'].format(d=day_name(t, upd_d), t=upd_t)}</span>{t['switch']}</div>
  <h1>{t['h1']}</h1>
  <p>{t['intro']}</p>
</section>
<div class="stale" id="n9gt-stale">{t['stale'].format(d=today)}</div>
<nav class="toc">{toc}</nav>

<section id="n9gt-rate">
<h2>{t['rate_h'].format(d=today)}</h2>
<p class="sub">{t['rate_sub'].format(g22=inr(g22), g24=inr(g24))}</p>
{table(t['rate_cols'], rate_rows, cls='rate', hide=(2, 4))}
{yday}
<p class="note">{rate_note}</p>
<p class="attr">{t['attr'].format(gp=SRC['gp'], fx=SRC['fx'])}</p>
</section>

<section id="n9gt-thermometer">
<h2>{t['therm_h']}</h2>
<div class="reading">
  <div class="gauge">{gauge(L, t)}<div class="legend">{legend}</div></div>
  <div>
    <p class="lab">{t['today_is']}</p>
    <div class="big bigname" style="color:{COLORS[band]}">{bname}</div>
    <p>{t['main'].format(x=x, dir=d, pct=p_)}</p>
    <p class="note">{t['band_text'][band]}</p>
    <a class="share" href="{share}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-3.9-4.7-4.1-.1-.2-1.1-1.5-1.1-2.8s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.3 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.5.1.3.6 1 1.3 1.7.9.8 1.7 1.1 2 1.2.2.1.4.1.5-.1l.7-.9c.2-.2.4-.2.6-.1l1.9.9c.3.1.4.2.5.3.1.2.1.7-.1 1.3z"/></svg>{t['share_b']}</a>
  </div>
</div>
<div class="cards cards3">
  <div class="card"><h3>{t['r_avg']}</h3><div class="v">{pct(s)}</div><p>{t['r_avg_sub'].format(a=month_name(t, L['avg12_from']) + ' – ' + month_name(t, L['avg12_to']), v=inr(L['avg12']))}</p></div>
  <div class="card"><h3>{t['r_yoy']}</h3><div class="v">{yoy}</div><p>{t['r_yoy_sub'].format(m=month_name(t, L['yoy_month']))}</p></div>
  <div class="card"><h3>{t['r_read']}</h3><div class="v"><span class="count" data-to="{p_}">{p_}</span> / 100</div><p>{t['r_read_sub']}</p></div>
</div>
<p class="note">{t['therm_note']}</p>
<h3>{t['past_h']}</h3>
<div class="box"><p style="margin:0">{past}</p><p class="note">{t['past_note']}</p></div>
</section>

<section id="n9gt-calculator">
<h2>{t['calc_h']}</h2>
<p class="sub">{t['calc_sub']}</p>
<div class="calc" id="n9gt-calc" data-rates='{rates_json}'>
  <div>
    <div class="row">
      <div class="f"><label for="n9c-w">{t['c_weight']}</label><input id="n9c-w" type="number" min="0" step="0.01" value="10" inputmode="decimal"></div>
      <div class="f"><label for="n9c-p">{t['c_purity']}</label><select id="n9c-p">{pur_opts}</select></div>
    </div>
    <div class="f"><label for="n9c-r">{t['c_rate']}</label><input id="n9c-r" type="number" min="0" step="1" value="{r22}" inputmode="decimal"></div>
    <div class="row">
      <div class="f"><label for="n9c-m">{t['c_making']}</label><input id="n9c-m" type="number" min="0" step="0.1" value="10" inputmode="decimal"></div>
      <div class="f"><label for="n9c-mt">&nbsp;</label><select id="n9c-mt"><option value="pct">{t['c_mtype'][0]}</option><option value="pg">{t['c_mtype'][1]}</option></select></div>
    </div>
    <div class="f"><label for="n9c-g">{t['c_gst']}</label><input id="n9c-g" type="number" min="0" step="0.1" value="3" inputmode="decimal"></div>
  </div>
  <div class="res" aria-live="polite">
    <div><span>{co[0]}</span><b id="n9o-g">₹{inr(c_gold)}</b></div>
    <div><span>{co[1]}</span><b id="n9o-m">₹{inr(c_make)}</b></div>
    <div><span>{co[2]}</span><b id="n9o-t">₹{inr(c_gst)}</b></div>
    <div class="tot"><span>{co[3]}</span><span id="n9o-b">₹{inr(c_tot)}</span></div>
    <div><span>{co[4]}</span><b id="n9o-pg">₹{inr(c_tot / 10)}</b></div>
  </div>
</div>
<p class="note">{t['c_note']}</p>
</section>

<section id="n9gt-chart">
<h2>{t['chart_h']}</h2>
<p class="sub">{t['chart_sub']}</p>
<div class="box chart">{chart(L, t)}</div>
<h3>{t['ribbon_h']}</h3>
<p class="sub">{t['ribbon_sub']}</p>
<div class="box chart">{ribbon(L, t)}<div class="legend">{legend}</div></div>
</section>

<section id="n9gt-returns">
<h2>{t['ret_h']}</h2>
<p class="sub">{t['ret_sub']}</p>
{table(t['ret_cols'], ret_rows, hide=(2,))}
<h3>{t['split_h']}</h3>
<p class="sub">{t['split_sub']}</p>
{table(t['split_cols'], split_rows, hide=(3,))}
<p class="note">{t['split_text'].format(s=s10v)}</p>
</section>

<section id="n9gt-history">
<h2>{t['hist_h']}</h2>
<p class="sub">{t['hist_sub'].format(y=cur['year'], n=cur['months'])}</p>
{table(t['hist_cols'], hist_rows, hide=(3, 4))}
<h3>{t['m12_h']}</h3>
{table(t['m12_cols'], m12_rows)}
{d30_html}
</section>

<section id="n9gt-drivers">
<h2>{t['drv_h']}</h2>
<ul>{''.join(f'<li>{x_.format(s=s10v)}</li>' for x_ in t['drv'])}</ul>
<h3>{t['india_h']}</h3>
<p>{t['india'].format(df=day_name(t, L['duty_from']))}</p>
</section>

<section id="n9gt-purity">
<h2>{t['pur_h']}</h2>
{table(t['pur_cols'], pur_rows, num_from=9)}
<p class="note">{t['hallmark']}</p>
<h3>{t['unit_h']}</h3>
{table(t['unit_cols'], unit_rows)}
</section>

<section id="n9gt-ways">
<h2>{t['ways_h']}</h2>
{table(t['ways_cols'], ways_rows, num_from=9)}
</section>

<section id="n9gt-how">
<h2>{t['how_h']}</h2>
<ol>{''.join(f'<li>{x_}</li>' for x_ in t['how'])}</ol>
{table(t['zones_h'], zones, num_from=9)}
<h3>{t['use_h']}</h3>
<ul>{''.join(f'<li>{x_}</li>' for x_ in t['use'])}</ul>
</section>

<section id="n9gt-faq">
<h2>{t['faq_h']}</h2>
{faq_html}
</section>

<h2>{t['rel_h']}</h2>
<div class="rel">{rel}</div>

<section class="cta">
  <h2>{t['cta_h']}</h2>
  <p>{t['cta']}</p>
  <a class="btn" href="{DEMO}" target="_blank" rel="noopener">{t['cta_b']}</a>
</section>

<p class="disc">{t['sources'].format(**SRC)}</p>
<p class="disc">{t['disc']}</p>
<script type="application/ld+json">
{ld}
</script>
<script>
(function(){{var box=document.querySelector("#n9gt .reading");if(!box)return;
if(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches)return;
var nums=document.querySelectorAll("#n9gt .count");box.classList.add("pre");nums.forEach(function(n){{n.textContent="0";}});
function go(){{box.classList.remove("pre");box.classList.add("go");
var nd=box.querySelector(".needle"),t0=null;requestAnimationFrame(function step(ts){{if(!t0)t0=ts;
var m=getComputedStyle(nd).transform,a=0;if(m&&m!=="none"){{var v=m.match(/-?[0-9.e]+/g);a=Math.atan2(+v[1],+v[0])*180/Math.PI;if(a<-90)a+=360;}}
var r=Math.max(0,Math.min(100,Math.round(a/1.8)));nums.forEach(function(n){{n.textContent=ts-t0>3300?n.getAttribute("data-to"):r;}});
if(ts-t0<=3300)requestAnimationFrame(step);}});}}
if("IntersectionObserver" in window){{var io=new IntersectionObserver(function(e){{if(e[0].isIntersecting){{io.disconnect();go();}}}},{{threshold:.35}});io.observe(box);}}else go();}})();
(function(){{var c=document.getElementById("n9gt-calc");if(!c)return;var R=JSON.parse(c.getAttribute("data-rates"));
function $(i){{return document.getElementById(i);}}function num(i){{var v=parseFloat($(i).value);return isFinite(v)&&v>0?v:0;}}
function f(v){{return "₹"+Math.round(v).toLocaleString("en-IN");}}
function calc(){{var w=num("n9c-w"),r=num("n9c-r"),m=num("n9c-m"),g=num("n9c-g"),gold=r/10*w,mk=$("n9c-mt").value==="pct"?gold*m/100:m*w,tx=(gold+mk)*g/100,tot=gold+mk+tx;
$("n9o-g").textContent=f(gold);$("n9o-m").textContent=f(mk);$("n9o-t").textContent=f(tx);$("n9o-b").textContent=f(tot);$("n9o-pg").textContent=w?f(tot/w):"–";}}
$("n9c-p").addEventListener("change",function(){{$("n9c-r").value=R[this.value];calc();}});
["n9c-w","n9c-r","n9c-m","n9c-g","n9c-mt"].forEach(function(i){{$(i).addEventListener("input",calc);$(i).addEventListener("change",calc);}});calc();}})();
(function(){{var r=document.getElementById("n9gt"),s=document.getElementById("n9gt-stale");if(!r||!s)return;
var d=new Date(r.getAttribute("data-updated")+"T00:00:00+05:30");if((Date.now()-d)/864e5>3)s.style.display="block";}})();
</script>
</div>
""".replace("§Y§", L["hist_from"][:4])


def main():
    L = json.loads((ROOT / "data" / "latest.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for lang in ("en", "hi"):
        (OUT / f"gold-thermometer-{lang}.html").write_text(page(L, lang), encoding="utf-8")
    print(f"OK: Gold Thermometer pages built for {L['date']} ({L['band']}, reading {round(L['percentile'])}).")


if __name__ == "__main__":
    main()
