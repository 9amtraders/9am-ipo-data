#!/usr/bin/env python3
"""Renders the IPO Allotment Status page for WordPress.

Reads   widget/allotment-page.html   the page template with N9AL placeholders
        ipos.json                    the IPO list built by build.py
Writes  build/allotment-page.html    the full page with the current IPO cards written in,
                                     so search engines see every IPO name without running JavaScript

The cards use the same rules as the page's own script, which refreshes them in the browser.
"""
import html
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = timezone(timedelta(hours=5, minutes=30))


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def d(s):
    return date.fromisoformat(s) if isinstance(s, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else None


def add_wd(x, n):
    while n > 0:
        x += timedelta(days=1)
        if x.weekday() < 5:
            n -= 1
    return x


def fmt(x):
    return f"{x.day} {x.strftime('%b')}" if x else "–"


def card(i, today, hour, reg, bse, nse):
    open_, close = d(i.get("open")), d(i.get("close"))
    if not open_ or not close:
        return None
    allot = d(i.get("allotment"))
    allot_est = allot is None
    allot = allot or add_wd(close, 1)
    credit = add_wd(allot, 1)
    listing = d(i.get("listing"))
    list_est = listing is None
    listing = listing or add_wd(close, 3)
    if today < open_ or (today - close).days > 12:
        return None
    if today <= close:
        st, cls, stage = f"Bidding open till {fmt(close)}", "open", 0
    elif today < allot or (today == allot and hour < 18):
        st, cls, stage = f"Allotment {'expected' if allot_est else 'on'} {fmt(allot)}", "wait", 1
    elif today < listing:
        st, cls, stage = "Allotment status is out", "out", 2
    else:
        st, cls, stage = f"Listed on {fmt(listing)}", "listed", 3

    tl = "".join(
        f'<div class="{"now" if k == stage else ""}"><b>{fmt(x)}{"*" if e else ""}</b>{lab}</div>'
        for k, (lab, x, e) in enumerate([("Closes", close, False), ("Allotment", allot, allot_est),
                                         ("Refund &amp; credit", credit, True), ("Listing", listing, list_est)]))
    sub, al = i.get("sub") or {}, i.get("allot") or {}
    sf = " when last checked" if sub and not sub.get("final") else ""
    ch = ""
    if al.get("oneIn") and al["oneIn"] <= 1 and sub.get("retail") is not None and sub["retail"] < 1:
        ch = (f'<p class="chance">Retail portion undersubscribed ({esc(sub["retail"])}x{sf}), '
              'so every valid retail application should get at least one lot.</p>')
    elif al.get("oneIn"):
        extra = f' ({esc(sub["retail"])}x retail subscription{sf})' if sub.get("retail") else ""
        ch = f'<p class="chance">Retail chance: about <b>1 in {esc(al["oneIn"])}</b> applications{extra}</p>'
    elif sub.get("retail"):
        ch = f'<p class="chance">Retail subscription: <b>{esc(sub["retail"])}x</b>{sf}</p>'

    r = reg.get(i.get("registrar") or "")
    if r:
        main = f'<a class="join" href="{esc(r[1])}" target="_blank" rel="noopener">Check on {esc(r[0])}</a>'
        alt = (f'<div class="row2"><a class="join alt" href="{bse}" target="_blank" rel="noopener">BSE</a>'
               f'<a class="join alt" href="{nse}" target="_blank" rel="noopener">NSE</a></div>')
    else:
        main = f'<a class="join" href="{bse}" target="_blank" rel="noopener">Check on BSE</a>'
        alt = (f'<a class="join alt" href="{nse}" target="_blank" rel="noopener">Check on NSE</a>'
               '<p class="handle">Registrar not confirmed yet. See the registrar table below.</p>')
    band = f'<span class="tag">{esc(i["band"])}</span>' if i.get("band") else ""
    key = esc((i["name"] + " " + " ".join(i.get("aka") or [])).lower())
    html_ = (f'<article class="card{" hot" if stage == 2 else ""}" data-n="{key}"><h3>{esc(i["name"])} IPO</h3>'
             f'<div class="tags"><span class="status {cls}">{esc(st)}</span><span class="tag">{esc(i.get("board"))}</span>{band}</div>'
             f'<div class="tl">{tl}</div>{ch}<div class="btns">{main}{alt}</div></article>')
    return stage, close, html_


def main():
    tpl = (ROOT / "widget" / "allotment-page.html").read_text(encoding="utf-8")
    data = json.loads((ROOT / "ipos.json").read_text(encoding="utf-8"))
    reg = json.loads(re.search(r"var REG=(\{.*?\});", tpl).group(1))
    bse = re.search(r'var BSE="([^"]+)"', tpl).group(1)
    nse = re.search(r'NSE="([^"]+)"', tpl).group(1)
    now = datetime.now(IST)
    cards = [c for c in (card(i, now.date(), now.hour, reg, bse, nse)
                         for i in data.get("ipos", []) if not i.get("archived")) if c]
    order = {2: 0, 1: 1, 0: 2, 3: 3}
    cards.sort(key=lambda c: (order[c[0]], -c[1].toordinal()))
    body = "".join(c[2] for c in cards) or (
        '<div class="loading">No IPOs are in the allotment window right now. '
        'Use the registrar table below for older issues.</div>')
    up = d(data.get("updated"))
    out = tpl.replace("<!--N9AL:CARDS-->", body).replace(
        "<!--N9AL:UPDATED-->", f"IPO list updated {fmt(up)} · * = expected date")
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "allotment-page.html").write_text(out, encoding="utf-8")
    print(f"OK: allotment page rendered with {len(cards)} IPO cards.")


if __name__ == "__main__":
    main()
