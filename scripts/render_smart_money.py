#!/usr/bin/env python3
"""
Renders the Smart Money Tracker page for WordPress.

Reads  smartmoney/deals.json  +  widget/smart-money-page.html (the page template)
Writes build/smart-money-page.html

Fills the template's SEO slots with plain HTML Google can read without
running JavaScript: today's date in the H1, today's bulk and block deal
tables, the biggest net buys/sells, accumulation streaks, and Dataset schema.
Save as scripts/render_smart_money.py in 9amtraders/9am-ipo-data.
"""
import html
import json
import datetime as dt
from pathlib import Path

DATA = Path("smartmoney/deals.json")
TPL = Path("widget/smart-money-page.html")
OUT = Path("build/smart-money-page.html")
PAGE_URL = "https://9amtraders.com/nse-bulk-and-block-deals-tracker/"
DATA_URL = "https://raw.githubusercontent.com/9amtraders/9am-ipo-data/main/smartmoney/deals.json"
TOP_ROWS = 20


def esc(v):
    return html.escape(str(v), quote=True)


def day(s, long=False):
    d = dt.date.fromisoformat(s)
    return d.strftime("%-d %B %Y" if long else "%-d %b %Y")


def cr(v, sign=False):
    a = abs(v)
    s = ("+" if v > 0 else "−" if v < 0 else "") if sign else ("−" if v < 0 else "")
    if a >= 1000:
        return f"{s}₹{a / 1000:.2f}K Cr"
    if a >= 100:
        return f"{s}₹{a:.0f} Cr"
    if a >= 1:
        return f"{s}₹{a:.1f} Cr"
    return f"{s}₹{a * 100:.0f} L"


def inr(n):
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def title(name):
    t = " ".join(w.capitalize() for w in name.lower().split())
    for w in ("Ltd", "Llp", "Pvt", "Huf", "Pte", "Llc", "Plc"):
        t = t.replace(f" {w}", f" {w.upper()}")
    return t


def stock_link(sym):
    return f'<a href="#stock-{esc(sym)}" data-sym="{esc(sym)}"><b>{esc(sym)}</b></a>'


def deal_table(rows):
    head = ("<tr><th>Stock</th><th>Investor</th><th>Action</th><th class='n'>Qty</th>"
            "<th class='n'>Price ₹</th><th class='n'>Value</th></tr>")
    body = "".join(
        f"<tr><td>{stock_link(r['s'])}<br><small class='mut'>{esc(r['n'])}</small></td>"
        f"<td><a href='#' data-inv='{esc(r['c'])}'>{esc(title(r['c']))}</a></td><td class='{'g' if r['b'] else 'r'}'><b>{'BUY' if r['b'] else 'SELL'}</b></td>"
        f"<td class='n'>{inr(r['q'])}</td><td class='n'>{r['p']:,.2f}</td><td class='n'>{cr(r['v'])}</td></tr>"
        for r in rows)
    return f"<div class='tw'><table>{head}{body}</table></div>"


def main():
    data = json.loads(DATA.read_text())
    tpl = TPL.read_text(encoding="utf-8")
    deals, dates = data.get("deals", []), data.get("dates", [])
    if not deals or not dates:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(tpl, encoding="utf-8")
        print("no deals yet — template written unchanged")
        return

    # same-day buy + sell of similar size by the same client = churn (mostly HFT)
    legs = {}
    for r in deals:
        r["v"] = r["q"] * r["p"] / 1e7
        k = (r["d"], r["s"], r["c"])
        legs.setdefault(k, [0, 0])[r["b"]] += r["q"]
    for r in deals:
        b0, b1 = legs[(r["d"], r["s"], r["c"])]
        r["ch"] = b0 > 0 and b1 > 0 and min(b0, b1) / max(b0, b1) >= 0.8
    real = [r for r in deals if not r["ch"]]

    latest = dates[0]
    today = sorted([r for r in real if r["d"] == latest], key=lambda r: -r["v"])
    bulk = [r for r in today if r["t"] == "BULK"][:TOP_ROWS]
    block = [r for r in today if r["t"] == "BLOCK"][:TOP_ROWS]
    sectors = data.get("sectors", {})

    net = {}
    for r in today:
        net[r["s"]] = net.get(r["s"], 0) + (r["v"] if r["b"] else -r["v"])
    buys = sorted([s for s in net if net[s] > 0], key=lambda s: -net[s])[:10]
    sells = sorted([s for s in net if net[s] < 0], key=lambda s: net[s])[:10]
    sec = {}
    for s, v in net.items():
        sec[sectors.get(s, "Other / SME")] = sec.get(sectors.get(s, "Other / SME"), 0) + v
    hot = max(sec, key=sec.get) if sec else None

    # accumulation streaks over the whole history
    st, sold = {}, set()
    for r in real:
        key = (r["c"], r["s"])
        if not r["b"]:
            sold.add(key)
            continue
        o = st.setdefault(key, {"days": set(), "v": 0})
        o["days"].add(r["d"])
        o["v"] += r["v"]
    streaks = sorted([(k, o) for k, o in st.items() if len(o["days"]) >= 2],
                     key=lambda x: (-len(x[1]["days"]), -x[1]["v"]))[:5]

    total = sum(r["v"] for r in today)
    nb = sum(1 for r in today if r["t"] == "BULK")
    nk = len(today) - nb
    summary = (f"On <b>{day(latest, True)}</b>, big investors traded <b>{cr(total)}</b> in {nb} bulk "
               f"deal{'s' * (nb != 1)} and {nk} block deal{'s' * (nk != 1)} across {len(net)} stocks on NSE.")
    if buys:
        summary += f" The biggest net buying was in {stock_link(buys[0])} ({cr(net[buys[0]], True)})"
        summary += (f", while {stock_link(sells[0])} saw the biggest exit ({cr(net[sells[0]], True)})."
                    if sells else ".")
    if hot and sec[hot] > 0:
        summary += f" Sector with the most money flowing in: <b>{esc(hot)}</b>."

    parts = [f'<section class="card in static" id="today">',
             f"<h2>Bulk and block deals today – {day(latest, True)}</h2>",
             f"<p style='margin:6px 0 4px'>{summary}</p>",
             f"<h3>Top bulk deals today ({day(latest)})</h3>",
             deal_table(bulk) if bulk else f"<p class='mut'>No bulk deals were reported on {day(latest)}.</p>",
             f"<h3>Block deals today ({day(latest)})</h3>",
             deal_table(block) if block else f"<p class='mut'>No block deals were reported on {day(latest)}.</p>"]
    if buys or sells:
        parts.append("<div class='grid2'>")
        parts.append("<div><h3>Stocks big money bought</h3><ol>" + "".join(
            f"<li>{stock_link(s)} <span class='g'>{cr(net[s], True)}</span></li>" for s in buys) + "</ol></div>")
        parts.append("<div><h3>Stocks big money sold</h3><ol>" + "".join(
            f"<li>{stock_link(s)} <span class='r'>{cr(net[s], True)}</span></li>" for s in sells) + "</ol></div>")
        parts.append("</div>")
    if streaks:
        parts.append("<h3>Accumulation streaks (last 3 months)</h3><ul>" + "".join(
            f"<li><a href='#' data-inv='{esc(c)}'>{esc(title(c))}</a> bought {stock_link(s)} on {len(o['days'])} different days "
            f"({cr(o['v'])} in total){'' if (c, s) in sold else ', with no sell deal reported'}.</li>"
            for (c, s), o in streaks) + "</ul>")
    parts.append(f"<p class='mut' style='font-size:12px'>Source: NSE bulk and block deals for "
                 f"{day(latest)}. Same-day buy-and-sell trades (mostly HFT) are left out.</p></section>")
    static = "\n".join(parts)

    schema = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": f"NSE bulk and block deals – {day(latest, True)}",
        "description": ("Daily NSE bulk deals and block deals with client name, buy or sell, quantity, "
                        "price and value, plus net money flow by stock and sector. Updated every trading day."),
        "url": PAGE_URL,
        "keywords": ["NSE bulk deals", "block deals today", "bulk deals today", "smart money", "NSE"],
        "dateModified": latest,
        "temporalCoverage": f"{dates[-1]}/{latest}",
        "isBasedOn": "https://www.nseindia.com/report-detail/display-bulk-and-block-deals",
        "creator": {"@type": "Organization", "name": "9AM Traders Academy", "url": "https://9amtraders.com/"},
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": DATA_URL}],
    }
    schema_html = ('<script type="application/ld+json">' +
                   json.dumps(schema, ensure_ascii=False).replace("</", "<\\/") + "</script>")

    out = (tpl.replace("<!--SM9:H1DATE-->",
                       f'<span style="display:block;font-size:.42em;color:#8f9bc0;font-weight:600;'
                       f'margin-top:10px;letter-spacing:0">Updated {day(latest, True)}</span>')
              .replace("<!--SM9:STATIC-->", static)
              .replace("<!--SM9:UPDATED-->", f"Last updated {esc(data.get('updated', latest))}. ")
              .replace("<!--SM9:SCHEMA-->", schema_html))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT} for {latest}: {len(bulk)} bulk, {len(block)} block rows")


if __name__ == "__main__":
    main()
