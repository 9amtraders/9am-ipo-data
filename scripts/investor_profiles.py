#!/usr/bin/env python3
"""
Big-investor profile pages (Smart Money) — nightly updater and renderer
-----------------------------------------------------------------------
Data:      smartmoney/investors/<slug>.json   (one file per investor; holdings are edited by hand each quarter)
Input:     smartmoney/deals.json              (NSE bulk & block deals + closing prices, built by build_smart_money.py)
Output:    build/investors/<slug>.html + build/investors/smart-money.html  (pasted into WordPress by publish_investor_pages.py)

Every trading day it:
  1. finds that day's NSE bulk/block deals made by each investor (matched on whole names, e.g. "VIJAY KEDIA",
     "KEDIA SECURITIES", "ABAKKUS") and saves them in the investor's file under auto_deals;
  2. refreshes the closing price behind every "on paper" gain, and adds a gain card for new buys;
  3. renders all pages.
Usage:  python scripts/investor_profiles.py            (update + render)
        python scripts/investor_profiles.py --render   (render only, no data changes)
Educational data only. Not a buy/sell recommendation.
"""
import json, glob, html, os, re, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "smartmoney" / "investors"
DEALS_FILE = ROOT / "smartmoney" / "deals.json"
OUT_DIR = ROOT / "build" / "investors"
CSS = (ROOT / "widget" / "investor-profile-style.html").read_text(encoding="utf-8")
JS = (ROOT / "widget" / "investor-profile-script.html").read_text(encoding="utf-8")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MAX_CARDS = 6          # gain cards per profile
AUTO_CARD_DAYS = 180   # new buys younger than this get an automatic "on paper" card
OTHERS = {}

# ---------------------------------------------------------------- dates & matching
MONTHS = {m: i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}

def show_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"

def sort_key(label):
    """'19 Oct 2026' / 'Oct 2026' / '2026-10-19' -> sortable tuple."""
    s = (label or "").strip()
    try:
        d = dt.date.fromisoformat(s); return (d.year, d.month, d.day)
    except ValueError:
        pass
    m = re.match(r"(?:(\d{1,2})\s+)?([A-Za-z]{3})[a-z]*\s+(\d{4})", s)
    if m:
        return (int(m.group(3)), MONTHS.get(m.group(2).title(), 1), int(m.group(1) or 15))
    return (0, 0, 0)

def words(s):
    return set(re.sub(r"[^A-Z0-9 ]+", " ", (s or "").upper()).split())

def matches(client, aliases):
    """True if every word of any alias appears in the client name (order free: 'KACHOLIA ASHISH' matches)."""
    cw = words(client)
    return any(words(a) <= cw for a in aliases)

# ---------------------------------------------------------------- update
def update(all_d):
    if not DEALS_FILE.exists():
        print("no smartmoney/deals.json — skipping deal update"); return
    feed = json.loads(DEALS_FILE.read_text())
    close, close_date = feed.get("close", {}), feed.get("closeDate")
    # extra closing prices for stocks behind gain cards (they may have no deal in the last 3 months)
    want = {p["sym"] for d in all_d for p in d.get("pl", []) if p.get("sym")} - set(close)
    if want and os.environ.get("PRICE_LOOKUP", "1") != "0":
        try:
            sys.path.insert(0, str(ROOT))
            from build_smart_money import latest_closes          # same NSE bhavcopy reader the tracker uses
            cd, extra = latest_closes(want)
            if extra:
                close = {**close, **extra}; close_date = close_date or cd
        except Exception as ex:  # noqa: BLE001
            print("price lookup skipped:", ex)
    today = dt.datetime.now(IST).date()
    for d in all_d:
        seen = {(x["d"], x["s"], x["b"], x["q"], x["p"]) for x in d.get("auto_deals", [])}
        added = 0
        for r in feed.get("deals", []):
            if not matches(r.get("c"), d.get("aliases", [])):
                continue
            k = (r["d"], r["s"], r["b"], r["q"], r["p"])
            if k in seen:          # same deal listed as BULK and BLOCK, or already saved
                continue
            seen.add(k); added += 1
            d.setdefault("auto_deals", []).append({"d": r["d"], "s": r["s"], "n": r["n"], "c": r["c"], "b": r["b"], "q": r["q"], "p": r["p"], "t": r["t"]})
        d["auto_deals"] = sorted(d.get("auto_deals", []), key=lambda x: x["d"], reverse=True)[:200]
        # refresh prices behind existing paper cards
        for p in d.get("pl", []):
            if p.get("type") == "paper" and p.get("sym") in close and close_date:
                p["now"] = close[p["sym"]]; p["now_date"] = show_date(close_date) + ", NSE close"
        # add paper cards for recent auto buys
        have = {p.get("sym") for p in d.get("pl", [])}
        for x in d["auto_deals"]:
            if x["b"] != 1 or x["s"] in have or x["s"] not in close or not close_date:
                continue
            if (today - dt.date.fromisoformat(x["d"])).days > AUTO_CARD_DAYS:
                continue
            d.setdefault("pl", []).insert(0, {"type": "paper", "stock": x["n"], "sym": x["s"], "qty": x["q"], "buy": x["p"],
                                              "date": show_date(x["d"]), "now": close[x["s"]], "now_date": show_date(close_date) + ", NSE close", "auto": True})
            have.add(x["s"])
        d["pl"] = d.get("pl", [])[:MAX_CARDS]
        d["deals_updated"] = show_date(today.isoformat())
        if added:
            print(f"{d['name']}: {added} new deal(s)")

# ---------------------------------------------------------------- merge for display
def merged_deals(d):
    """Hand-entered deals + deals found automatically, newest first, without duplicates."""
    out = [dict(x) for x in d.get("deals", [])]
    sig = {(round(x["qty"]), round(x["price"], 2)) for x in out}
    for x in d.get("auto_deals", []):
        if (x["q"], round(x["p"], 2)) in sig:
            continue
        sig.add((x["q"], round(x["p"], 2)))
        own_name = words(d["name"]) <= words(x["c"])
        out.append({"date": show_date(x["d"]), "stock": x["n"], "action": "Buy" if x["b"] else "Sell", "qty": x["q"], "price": x["p"],
                    "via": "" if own_name else x["c"].title()})
    return sorted(out, key=lambda x: sort_key(x["date"]), reverse=True)

def refresh_latest_stat(d, deals):
    if not deals: return
    x = deals[0]
    for s in d.get("stats", []):
        if s["label"] == "Latest deal":
            verb = "Bought" if x["action"].lower().startswith("buy") else "Sold"
            s["value"] = x["date"]; s["sub"] = f"{verb} {x['stock']} · {cr(x['qty'] * x['price'], 1)}"

SITE = "https://9amtraders.com"
e = html.escape

def inr(n, dec=0):
    """Indian digit grouping: 1234567 -> 12,34,567"""
    neg = n < 0; n = abs(n)
    s = f"{n:.{dec}f}"; whole, _, frac = s.partition('.')
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        whole = ','.join(parts + [tail])
    return ('-' if neg else '') + whole + ('.' + frac if frac else '')

def cr(rupees, dec=2):
    v = rupees / 1e7
    return ('−' if v < 0 else '') + '₹' + inr(abs(v), dec) + ' Cr'

BADGE = {'ex': '<em class="ex">Exact</em>', 'es': '<em class="es">Est.</em>', 'nd': '<em class="nd">Not public</em>'}

def deals_section(d):
    if not d.get('deals'):
        return f'''<section class="sec rv" aria-labelledby="h-deals"><h2 id="h-deals">Recent bets: bulk deals</h2>
<p class="lede" style="margin:0">{e(d.get("no_deals_text","No bulk or block deals by this investor were found in 2026."))} We check NSE every trading day and add new deals here automatically (last checked {e(d.get("deals_updated", d["updated"]))}).</p></section>'''
    rows = ''
    for x in d['deals']:
        act = x['action']; cls = 'buy' if act.lower().startswith('buy') else 'sell'
        val = x['qty'] * x['price']
        who = f'<br><small style="color:#5b6278">{e(x["via"])}</small>' if x.get('via') else ''
        rows += (f'<tr><td>{e(x["date"])}</td><td>{e(x["stock"])}{who}</td><td><span class="{cls}">{e(act)}</span></td>'
                 f'<td class="n">{inr(x["qty"])}</td><td class="n">₹{inr(x["price"],2)}</td><td class="n">{cr(val)}</td><td>{BADGE["ex"]}</td></tr>')
    note = f'<p class="note">Deal value = shares × average price. New deals are added automatically from NSE every trading day (last checked {e(d.get("deals_updated", d["updated"]))}). {e(d.get("deals_note",""))}</p>'
    return f'''<section class="sec rv" aria-labelledby="h-deals"><h2 id="h-deals">Recent bets: bulk deals</h2>
<p class="lede">Bulk and block deals are the only place where an investor's buy or sell price is published. These are {e(d["name"])}'s recent deals as reported in exchange data.</p>
<div class="tw"><table><thead><tr><th>Date</th><th>Stock</th><th>Action</th><th class="n">Shares</th><th class="n">Price</th><th class="n">Deal value</th><th>Price type</th></tr></thead><tbody>{rows}</tbody></table></div>{note}</section>'''

def pl_card(p):
    """Types: paper (buy price + recent price), sale (cash from a sale), static (given text)."""
    if p['type'] == 'paper':
        gain = (p['now'] - p['buy']) * p['qty']; pct = (p['now'] / p['buy'] - 1) * 100
        kind = 'pos' if gain >= 0 else 'neg'
        big = ('+' if gain >= 0 else '') + cr(gain)
        m = f'{"+" if pct>=0 else "−"}{abs(pct):.1f}% on paper at ₹{inr(p["now"],2)} ({e(p["now_date"])}){(", " + e(p["extra"])) if p.get("extra") else ""} {BADGE["es"]}'
        k = f'Bought {inr(p["qty"])} @ ₹{inr(p["buy"],2)} · {e(p["date"])}'
    elif p['type'] == 'sale':
        kind = 'neu'; big = cr(p['qty'] * p['price']); k = f'Sold {inr(p["qty"])} @ ₹{inr(p["price"],2)} · {e(p["date"])}'
        m = f'{e(p.get("extra","Cash from the sale."))} {BADGE["nd"] if p.get("badge","nd")=="nd" else BADGE["es"]}'
    else:
        kind = p.get('kind', 'neu'); big = e(p['big']); k = e(p['k']); m = f'{e(p["m"])} {BADGE[p.get("badge","nd")]}'
    return f'<div class="plc {kind}"><h3>{e(p["stock"])}</h3><div class="k">{k}</div><div class="big">{big}</div><div class="m">{m}</div></div>'

def changes_section(d):
    c = d['changes']
    def col(cls, title, items):
        li = ''.join(f'<li>{e(i)}</li>' for i in items) or '<li>None this quarter</li>'
        return f'<div class="cq {cls}"><b>{title}</b><ul>{li}</ul></div>'
    note = f'<p class="note">{e(d["changes_note"])}</p>' if d.get('changes_note') else ''
    return f'''<section class="sec rv" aria-labelledby="h-qchg"><h2 id="h-qchg">What changed in the {e(d["quarter"])} quarter</h2>
<p class="lede">Compared with the previous quarter's shareholding filings.</p>
<div class="chg4">{col("q-new","New buys",c.get("new",[]))}{col("q-add","Added",c.get("add",[]))}{col("q-cut","Reduced",c.get("cut",[]))}{col("q-out","Exited / below 1%",c.get("out",[]))}</div>{note}</section>'''

CHIP = {'same': 'c-same', 'new': 'c-new', 'add': 'c-add', 'cut': 'c-cut', 'out': 'c-out'}
def holdings_section(d):
    rows = ''
    for h in d['holdings']:
        t, txt = h['chg']
        gain = h.get('gain', '<em class="nd">Buy price not public</em>')
        rows += (f'<tr><td>{e(h["stock"])}</td><td class="n">{inr(h["qty"]) if h.get("qty") else "—"}</td><td class="n">{e(h["stake"])}</td>'
                 f'<td><span class="chip {CHIP[t]}">{e(txt)}</span></td><td class="n">{("₹"+inr(h["value_cr"],1)+" Cr") if h.get("value_cr") is not None else "Not shown"}</td><td>{gain}</td></tr>')
    return f'''<section class="sec rv" aria-labelledby="h-hold"><h2 id="h-hold">{e(d["name"])}'s current holdings: top {len(d["holdings"])} by value</h2>
<p class="lede">{e(d["holdings_lede"])}</p>
<div class="tw"><table><thead><tr><th>Stock</th><th class="n">Shares</th><th class="n">Stake</th><th>vs last quarter</th><th class="n">Value now</th><th>Est. gain</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">{e(d["holdings_note"])}</p></section>'''

def timeline_section(d):
    t = d.get('timeline')
    if not t: return ''
    mx = max(x['value'] for x in t)
    bars = ''.join(f'<div class="bar"><b>{e(x["label_value"])}</b><i data-h="{round(x["value"]/mx*100)}"></i></div>' for x in t)
    labels = ''.join(f'<span>{e(x["when"])}{" " + BADGE["es"] if x.get("est") else ""}</span>' for x in t)
    cols = f'style="grid-template-columns:repeat({len(t)},1fr)"'
    return f'''<section class="sec rv" aria-labelledby="h-time"><h2 id="h-time">Portfolio value over time</h2><p class="lede">Disclosed holdings only, as reported at each date.</p>
<div class="bars" id="smp-bars" aria-hidden="true" {cols}>{bars}</div><div class="bl" {cols}>{labels}</div></section>'''

def page(d):
    stats = ''.join(f'<div><small>{e(s["label"])}</small><b>{e(s["value"])}</b><span>{e(s["sub"])}{" " + BADGE["es"] if s.get("est") else ""}</span></div>' for s in d['stats'])
    pl = ''
    if d.get('pl'):
        pl = f'''<section class="sec rv" aria-labelledby="h-pl"><h2 id="h-pl">How much did those bets make?</h2>
<p class="lede">For buys with a known price, we compare the deal price with a recent market price. For sells, the sale amount is exact, but the profit is unknown unless the original buy price was also disclosed.</p>
<div class="pl">{"".join(pl_card(p) for p in d["pl"])}</div>
<p class="note">"On paper" means the gain or loss if the shares were sold at that price. It excludes brokerage, taxes and any later trades we cannot see.</p></section>'''
    news = ''.join(f'<a class="nw" href="{e(n["url"])}" target="_blank" rel="noopener nofollow"><small>{e(n["src"])} · {e(n["date"])}</small><b>{e(n["title"])}</b></a>' for n in d['news'])
    faq = ''.join(f'<div class="q"><h3>{e(q)}</h3><p>{e(a)}</p></div>' for q, a in d['faq'])
    src = ''.join((f'<li><a href="{e(s[1])}" target="_blank" rel="noopener nofollow">{e(s[0])}</a></li>' if s[1] else f'<li>{e(s[0])}</li>') for s in d['sources'])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ProfilePage", "name": d['h1'], "dateModified": d['updated_iso'],
         "mainEntity": {"@type": "Person", "name": d['name'], "description": d['schema_desc']}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "9AM Traders", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Smart Money", "item": SITE + "/smart-money/"},
            {"@type": "ListItem", "position": 3, "name": d['h1']}]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d['faq']]}]}
    return f'''<!-- 9AM Smart Money · Investor profile: {e(d["name"])} · generated from data/{d["slug"]}.json (paste into one Elementor HTML widget)
     SEO title: {d["meta"]["title"]}
     Meta description: {d["meta"]["description"]}
     Focus keywords: {d["meta"]["keywords"]}
     URL: {SITE}/smart-money/{d["slug"]}/ -->
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
{CSS}
<div class="smp" id="smp"><div class="w">
<nav class="crumb" aria-label="Breadcrumb"><a href="{SITE}/">9AM Traders</a> / <a href="{SITE}/smart-money/">Smart Money</a> / {e(d["category"])} / {e(d["name"])}</nav>
<header class="hero rv"><div class="hrow"><div class="av" aria-hidden="true">{e(d["initials"])}</div><div>
<span class="tag"><i></i>{e(d["tag"])}</span><h1>{e(d["h1"])}</h1><p>{e(d["intro"])}</p></div></div>
<div class="stats">{stats}</div></header>
<div class="legend rv"><span><em class="ex">Exact</em> price comes from an exchange bulk-deal record</span><span><em class="es">Est.</em> calculated from public data, may differ</span><span><em class="nd">Not public</em> no disclosed price, so no profit shown</span></div>
{deals_section(d)}
{pl}
{changes_section(d)}
{holdings_section(d)}
{timeline_section(d)}
<section class="sec rv" aria-labelledby="h-about"><h2 id="h-about">About {e(d["name"])}</h2><p class="lede" style="margin:0">{e(d["about"])}</p></section>
<section class="sec rv" aria-labelledby="h-news"><h2 id="h-news">In the news</h2><div class="news">{news}</div></section>
<section class="cta rv"><div><h2>Learn to read this data yourself</h2><p>Bulk deals, shareholding filings and FII/DII flows are taught in our live classes at 9AM Traders Academy, Delhi.</p></div><a href="https://wa.me/919315906004?text=Hi%2C%20I%20saw%20the%20smart%20money%20page%20and%20want%20a%20free%20demo%20class" target="_blank" rel="noopener">Book a free demo class</a></section>
<section class="sec rv" aria-labelledby="h-faq"><h2 id="h-faq">{e(d["name"])} portfolio: questions answered</h2><div class="faq">{faq}</div></section>
<section class="sec rv" aria-labelledby="h-more"><h2 id="h-more">More big investors</h2><div class="news">{OTHERS.get(d["slug"],"")}</div></section>
<section class="sec rv" aria-labelledby="h-src"><h2 id="h-src">Sources</h2><ol class="src">{src}</ol></section>
<p class="disc rv">Holdings as of the {e(d["quarter"])} filings (collected {e(d["updated"])}). Deals and prices last updated {e(d.get("deals_updated", d["updated"]))}. This page shows information that is publicly disclosed to the stock exchanges, collected for education. It is not investment advice, and it is not a recommendation to buy or sell any security or to copy any investor. Disclosed holdings cover only stakes above 1%, so the real portfolio may be larger or different. "Estimated" and "on paper" figures are our calculations from public data and may not match the investor's actual gains. 9AM Traders Academy is not connected with {e(d["name"])}. Spotted an error? Write to info@9amtraders.com and we will correct it.</p>
</div></div>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{JS}'''

def index_page(all_d):
    cards = ''
    for d in all_d:
        cards += (f'<a class="nw" href="{SITE}/smart-money/{d["slug"]}/"><small>{e(d["category"])} · {e(d["stats"][0]["value"])}</small>'
                  f'<b>{e(d["name"])} portfolio</b><span style="display:block;font-size:13px;color:#5b6278;margin-top:4px">{e(d["card_line"])}</span></a>')
    return f'''<!-- 9AM Smart Money · Big investors index (paste into one Elementor HTML widget). URL: {SITE}/smart-money/
     SEO title: Superstar Investor Portfolios 2026: Kacholia, Kedia, Jhunjhunwala & More | 9AM Traders
     Meta description: Latest portfolios of India's top 15 investors: disclosed holdings, new buys and sells, bulk deals with exact prices and estimated gains. Updated every quarter.
     Focus keywords: superstar investor portfolio, ace investor portfolio, hni portfolio india, big investor holdings -->
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
{CSS}
<div class="smp" id="smp"><div class="w">
<header class="hero rv"><div><span class="tag"><i></i>Smart Money · Updated {e(all_d[0]["updated"])}</span><h1>Big investors' portfolios: what they bought, sold and made</h1>
<p>Disclosed holdings, bulk deals with exact prices and the estimated gain on recent bets, for India's best-known investors. Every figure links to its source.</p></div></header>
<section class="sec rv"><h2>Big investors (HNIs)</h2><p class="lede">Tap a name to open the full profile.</p><div class="news">{cards}</div></section>
<p class="disc rv">For education only. Not investment advice or a recommendation to copy any investor.</p>
</div></div>
{JS}'''


def latest_strip(all_d):
    rows = []
    for d in all_d:
        for x in merged_deals(d)[:3]:
            rows.append((sort_key(x["date"]), d, x))
    rows.sort(key=lambda r: r[0], reverse=True)
    items = ''.join(f'<a class="nw" href="{SITE}/smart-money/{d["slug"]}/"><small>{e(x["date"])} · {e(d["name"])}</small><b>{"Bought" if x["action"].lower().startswith("buy") else "Sold"} {e(x["stock"])}</b><span style="display:block;font-size:13px;color:#5b6278;margin-top:4px">{inr(x["qty"])} shares @ ₹{inr(x["price"],2)} · {cr(x["qty"]*x["price"],1)}</span></a>' for _, d, x in rows[:9])
    return f'<section class="sec rv"><h2>Latest big-investor deals</h2><p class="lede">From NSE bulk and block deals, updated every trading day.</p><div class="news">{items}</div></section>'


def main():
    render_only = "--render" in sys.argv
    files = sorted(DATA_DIR.glob("*.json"))
    all_d = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    if not render_only:
        update(all_d)
        for f, d in zip(files, all_d):
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    all_d.sort(key=lambda d: d.get("order", 99))
    for d in all_d:
        OTHERS[d['slug']] = ''.join(f'<a class="nw" href="{SITE}/smart-money/{o["slug"]}/"><small>{e(o["category"])}</small><b>{e(o["name"])} portfolio</b></a>' for o in all_d if o['slug'] != d['slug'])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for d in all_d:
        view = dict(d); view["deals"] = merged_deals(d); refresh_latest_stat(view, view["deals"])
        (OUT_DIR / f"{d['slug']}.html").write_text(page(view), encoding="utf-8")
    views = []
    for d in all_d:
        v = dict(d); v["deals"] = merged_deals(d); views.append(v)
    idx = index_page(all_d).replace('<section class="sec rv"><h2>Big investors (HNIs)</h2>', latest_strip(views) + '<section class="sec rv"><h2>Big investors (HNIs)</h2>', 1)
    (OUT_DIR / "smart-money.html").write_text(idx, encoding="utf-8")
    print(f"rendered {len(all_d)} profiles + index into {OUT_DIR}")


if __name__ == "__main__":
    main()
