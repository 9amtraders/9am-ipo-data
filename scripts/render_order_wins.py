#!/usr/bin/env python3
"""
Renders the Order Wins Tracker page for WordPress.

Reads  orders/orders.json  +  widget/order-wins-page.html (the page template)
Writes build/order-wins-page.html with plain-HTML SEO content Google can read
without JavaScript: date in the H1, today's and this week's order tables,
game-changer orders, repeat winners, and Dataset schema.
Save as scripts/render_order_wins.py in 9amtraders/9am-ipo-data.
"""
import html
import os
import re
import json
import datetime as dt
from pathlib import Path

DATA = Path("orders/orders.json")
TPL = Path("widget/order-wins-page.html")
OUT = Path("build/order-wins-page.html")
PAGE_URL = "https://9amtraders.com/bse-order-wins-tracker-companies-that-bagged-new-orders-this-week/"
DATA_URL = "https://raw.githubusercontent.com/9amtraders/9am-ipo-data/main/orders/orders.json"
CT = {"govt": "Govt / PSU", "private": "Private", "overseas": "Overseas"}


def esc(v):
    return html.escape(str(v or ""), quote=True)


def day(s, long=False):
    return dt.date.fromisoformat(s).strftime("%-d %B %Y" if long else "%-d %b %Y")


def cr(v):
    if not v:
        return "n/a"
    if v >= 1000:
        return f"₹{v / 1000:.2f}K Cr"
    if v >= 100:
        return f"₹{v:.0f} Cr"
    if v >= 1:
        return f"₹{v:.1f} Cr"
    return f"₹{v * 100:.0f} L"


def name(o):
    return o.get("s") or o["n"]


def co_link(o):
    key = (o.get("s") or o["c"]).lower()
    return f'<a href="#company-{esc(key)}" data-co="{esc(o["c"])}"><b>{esc(name(o))}</b></a>'


def table(rows, mcap):
    head = ("<tr><th>Date</th><th>Company</th><th class='n'>Order value</th><th class='n'>% of mcap</th>"
            "<th>Client</th><th>Filing</th></tr>")
    body = []
    for o in rows:
        pm = o["v"] / mcap[o["c"]] * 100 if o["v"] and mcap.get(o["c"]) else None
        pdf = f'<a href="{esc(o["u"])}" target="_blank" rel="noopener">PDF</a>' if o.get("u") else ""
        body.append(
            f"<tr><td>{day(o['d'])}</td><td>{co_link(o)}<br><small class='mut'>{esc(o['h'][:140])}</small></td>"
            f"<td class='n'>{cr(o['v'])}</td><td class='n'>{f'{pm:.1f}%' if pm is not None else '—'}</td>"
            f"<td>{esc(o.get('cl') or '—')}<br><small class='mut'>{CT.get(o.get('ct'), '')} · {esc(o.get('th'))}</small></td>"
            f"<td>{pdf}</td></tr>")
    return f"<div class='tw'><table>{head}{''.join(body)}</table></div>"


def finish(page):
    """Point the CSS/JS links at this exact commit (fresh on every publish) and keep
    JSON-LD on one line so WordPress can't slip <p> tags into it."""
    page = page.replace("{{ASSET_VER}}", os.environ.get("GITHUB_SHA", "main"))

    def one_line(m):
        try:
            data = json.loads(m.group(1))
        except ValueError:
            return m.group(0)
        return ('<script type="application/ld+json">' +
                json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    page = re.sub(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', one_line, page, flags=re.S)
    return re.sub(r"\n\s*\n+", "\n", page)       # blank lines are where WordPress adds <p>


def main():
    data = json.loads(DATA.read_text())
    tpl = TPL.read_text(encoding="utf-8")
    orders = data.get("orders", [])
    OUT.parent.mkdir(exist_ok=True)
    if not orders:
        OUT.write_text(finish(tpl), encoding="utf-8")
        print("no orders yet — template written unchanged")
        return
    mcap = data.get("mcap", {})
    for o in orders:
        o["v"] = float(o.get("v") or 0)
    dates = sorted({o["d"] for o in orders}, reverse=True)
    latest = dates[0]
    week = set(dates[:5])
    today = sorted([o for o in orders if o["d"] == latest], key=lambda o: -o["v"])
    wk = sorted([o for o in orders if o["d"] in week], key=lambda o: -o["v"])
    big = [o for o in wk if o["v"] and mcap.get(o["c"]) and o["v"] / mcap[o["c"]] >= 0.10][:10]
    by = {}
    for o in orders:
        by.setdefault(o["c"], []).append(o)
    rep = sorted([(c, l) for c, l in by.items() if len(l) > 1],
                 key=lambda x: (-len(x[1]), -sum(o["v"] for o in x[1])))[:8]

    tot = sum(o["v"] for o in today)
    gov = sum(o["v"] for o in today if o.get("ct") == "govt")
    cos = len({o["c"] for o in today})
    summ = (f"On <b>{day(latest, True)}</b>, {cos} listed compan{'y' if cos == 1 else 'ies'} announced "
            f"{len(today)} new order{'s' * (len(today) != 1)} on BSE")
    summ += (f", worth at least <b>{cr(tot)}</b>" + (f" ({round(gov / tot * 100)}% from government and PSU clients)" if gov else "")
             if tot else "") + "."
    top = next((o for o in today if o["v"]), None)
    if top:
        summ += f" The biggest was {co_link(top)} with {cr(top['v'])}" + (f" from {esc(top['cl'])}" if top.get("cl") else "") + "."

    parts = ['<section class="card in static" id="today">',
             f"<h2>Order wins today – {day(latest, True)}</h2>",
             f"<p style='margin:6px 0 4px'>{summ}</p>",
             f"<h3>Companies that won orders today ({day(latest)})</h3>", table(today[:25], mcap),
             f"<h3>Biggest order wins this week</h3>", table(wk[:20], mcap)]
    if big:
        parts.append("<h3>Game-changer orders this week (10%+ of market cap)</h3><ul>" + "".join(
            f"<li>{co_link(o)} won an order of {cr(o['v'])}, about {o['v'] / mcap[o['c']] * 100:.0f}% of its market cap"
            + (f", from {esc(o['cl'])}" if o.get("cl") else "") + f" ({day(o['d'])}).</li>" for o in big) + "</ul>")
    if rep:
        parts.append("<h3>Repeat order winners (last 3 months)</h3><ul>" + "".join(
            f"<li>{co_link(l[0])}: {len(l)} orders" + (f" worth {cr(sum(o['v'] for o in l))}" if any(o['v'] for o in l) else "")
            + ".</li>" for c, l in rep) + "</ul>")
    parts.append(f"<p class='mut' style='font-size:12px'>Source: BSE corporate announcements, Award of Order / "
                 f"Receipt of Order, up to {day(latest)}. Values read from filing summaries — open the PDF to confirm.</p></section>")

    schema = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": f"BSE order wins – {day(latest, True)}",
        "description": ("Order wins and contracts announced by listed Indian companies on BSE: company, order value, "
                        "client, order as % of market cap and stock reaction. Updated through every trading day."),
        "url": PAGE_URL,
        "keywords": ["order win stocks today", "BSE order wins", "companies that bagged orders", "order book"],
        "dateModified": latest, "temporalCoverage": f"{dates[-1]}/{latest}",
        "isBasedOn": "https://www.bseindia.com/corporates/ann.html",
        "creator": {"@type": "Organization", "name": "9AM Traders Academy", "url": "https://9amtraders.com/"},
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": DATA_URL}],
    }
    out = (tpl.replace("<!--OW9:H1DATE-->",
                       f'<span style="display:block;font-size:.42em;color:#8f9bc0;font-weight:600;margin-top:10px;'
                       f'letter-spacing:0">Updated {day(latest, True)}</span>')
              .replace("<!--OW9:STATIC-->", "\n".join(parts))
              .replace("<!--OW9:UPDATED-->", f"Last updated {esc(data.get('updated', latest))}. ")
              .replace("<!--OW9:SCHEMA-->", '<script type="application/ld+json">'
                       + json.dumps(schema, ensure_ascii=False).replace("</", "<\\/") + "</script>"))
    out = finish(out)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT} for {latest}: {len(today)} today, {len(wk)} this week")


if __name__ == "__main__":
    main()
