#!/usr/bin/env python3
"""Renders the IPO GMP Today page (with the GMP Reality Check) for WordPress.

Reads   widget/gmp-page.html   the page template with N9GM placeholders
        ipos.json              the IPO list built by build.py (dates, band, subscription, score, allotment chance)
        gmp.json               grey market premium readings and listing results (written by the daily update)
Writes  build/gmp-page.html    the full page with every table written in, so search engines see it without JavaScript

gmp.json shape:
{
  "updated": "2026-11-03",
  "ipos": {
    "<id>": {                                  # same id as raw/ and reports/ (build.py slug)
      "name": "HGS (India)",
      "issuePrice": 120,                       # final issue price (upper band); optional, else taken from ipos.json band
      "readings": [                            # one per day, oldest first, rupees per share
        {"date": "2026-11-03", "low": 18, "high": 25, "sources": ["https://...", "https://..."]}
      ],
      "listing": {"date": "2026-11-06", "open": 131.5, "source": "https://..."}   # listing-day opening price, once listed
    }
  }
}
"""
import html
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = timezone(timedelta(hours=5, minutes=30))
CLOSE_PTS = 5.0          # within 5 percentage points = "Close"
BAR_MIN, BAR_MAX = -20.0, 100.0


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def slug(name):
    s = re.sub(r"\b(ltd|limited|ipo|pvt|private|the|and)\b", " ", str(name).lower().replace("&", " "))
    return re.sub(r"[^a-z0-9]+", "", s)


def d(s):
    return date.fromisoformat(s) if isinstance(s, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else None


def fmt(x):
    return f"{x.day} {x.strftime('%b')}" if x else "–"


def rs(v, dec=0):
    if v is None:
        return "–"
    s = f"{abs(v):,.{dec}f}"
    return ("-₹" if v < 0 else "₹") + s


def pct(v):
    return "–" if v is None else f"{v:+.1f}%"


def upper_band(band):
    nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+(?:\.\d+)?", band or "")]
    return max(nums) if nums else None


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def readings_of(g):
    out = []
    for r in (g or {}).get("readings") or []:
        lo, hi, dt = num(r.get("low")), num(r.get("high")), d(r.get("date"))
        if dt and lo is not None:
            hi = lo if hi is None else hi
            out.append((dt, min(lo, hi), max(lo, hi)))
    return sorted(out)


def score_cell(i):
    sc = i.get("score")
    if not isinstance(sc, (int, float)):
        return '<span class="fl">–</span>'
    k = "s4" if sc >= 75 else "s3" if sc >= 50 else "s2" if sc >= 25 else "s1"
    return f'<a class="sc {k}" href="https://9amtraders.com/ipo-analyzer-india/">{int(round(sc))}/100</a>'


def live_row(i, g, today):
    issue = num((g or {}).get("issuePrice")) or upper_band(i.get("band"))
    rd = readings_of(g)
    cur = rd[-1] if rd else None
    prev = rd[-2] if len(rd) > 1 else None
    if cur:
        lo, hi = cur[1], cur[2]
        mid = (lo + hi) / 2
        gtxt = rs(lo) if lo == hi else f"{rs(lo)} – {rs(hi)}"
        cls = "up" if mid > 0 else "dn" if mid < 0 else "fl"
        gmp = f'<span class="gmp {cls}">{gtxt}</span>'
        if cur[0] < today - timedelta(days=3):
            gmp += f'<br><small class="fl">as of {fmt(cur[0])}</small>'
        if prev:
            ch = mid - (prev[1] + prev[2]) / 2
            trend = (f'<span class="up">▲ {rs(ch)}</span>' if ch > 0 else
                     f'<span class="dn">▼ {rs(-ch)}</span>' if ch < 0 else '<span class="fl">No change</span>')
        else:
            trend = '<span class="fl">–</span>'
        if issue:
            est = f'{rs(issue + mid)}<br><small class="{cls}">{pct(mid / issue * 100)}</small>'
        else:
            est = "–"
    else:
        gmp, trend, est = '<span class="fl">No quote yet</span>', '<span class="fl">–</span>', "–"

    sub, al = i.get("sub") or {}, i.get("allot") or {}
    subs = f'{sub["total"]}x' if num(sub.get("total")) is not None else "–"
    if num(sub.get("total")) is not None and not sub.get("final"):
        subs += '<br><small class="fl">live</small>'
    chance = f'1 in {al["oneIn"]}' if al.get("oneIn") else "–"

    listing = d(i.get("listing"))
    close = d(i.get("close"))
    stage = ("Bidding open" if close and today <= close else
             f"Lists {fmt(listing)}" if listing else "Awaiting listing")
    key = esc(re.sub(r"[^a-z0-9 ]", "", (i["name"] + " " + " ".join(i.get("aka") or [])).lower()))
    return (f'<tr data-n="{key}"><td><b class="nm">{esc(i["name"])} IPO GMP</b>'
            f'<span class="tag">{esc(i.get("board") or "")}</span><span class="tag">{esc(stage)}</span></td>'
            f'<td class="n">{esc(i.get("band") or "–")}</td><td class="n">{gmp}</td><td class="n">{trend}</td>'
            f'<td class="n">{est}</td><td class="n">{subs}</td><td class="n">{chance}</td><td>{score_cell(i)}</td></tr>')


def bar_pos(v):
    v = max(BAR_MIN, min(BAR_MAX, v))
    return (v - BAR_MIN) / (BAR_MAX - BAR_MIN) * 100


def reality(gmp, ipos_by_id):
    rows = []
    for gid, g in (gmp.get("ipos") or {}).items():
        lst = g.get("listing") or {}
        ldate, lopen = d(lst.get("date")), num(lst.get("open"))
        i = ipos_by_id.get(gid, {})
        issue = num(g.get("issuePrice")) or upper_band(i.get("band"))
        rd = [r for r in readings_of(g) if ldate and r[0] < ldate]
        if not (ldate and lopen and issue and rd):
            continue
        last = rd[-1]
        said = (last[1] + last[2]) / 2 / issue * 100
        actual = (lopen - issue) / issue * 100
        rows.append((ldate, g.get("name") or i.get("name") or gid, said, actual, issue, lopen))
    rows.sort(key=lambda r: r[0], reverse=True)
    return rows


def main():
    tpl = (ROOT / "widget" / "gmp-page.html").read_text(encoding="utf-8")
    data = json.loads((ROOT / "ipos.json").read_text(encoding="utf-8"))
    gp = ROOT / "gmp.json"
    gmp = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else {"ipos": {}}
    problems = []
    for gid, g in (gmp.get("ipos") or {}).items():
        if not re.fullmatch(r"[a-z0-9]+", gid):
            problems.append(f"gmp.json: id '{gid}' must be lowercase letters and digits")
        for r in g.get("readings") or []:
            if not d(r.get("date")) or num(r.get("low")) is None:
                problems.append(f"gmp.json: {gid} has a reading without a valid date or low value: {r}")
    if problems:
        print("\n".join(problems))
        sys.exit(1)

    now = datetime.now(IST)
    today = now.date()
    ipos = [i for i in data.get("ipos", []) if not i.get("archived")]
    by_id = {slug(i["name"]): i for i in ipos}
    gi = gmp.get("ipos") or {}

    live, upcoming = [], []
    for i in ipos:
        op, cl, li = d(i.get("open")), d(i.get("close")), d(i.get("listing"))
        if not op:
            continue
        if op > today:
            if (op - today).days <= 30:
                upcoming.append(i)
        elif (li and today < li) or (not li and cl and (today - cl).days <= 5):
            live.append(i)
    live.sort(key=lambda i: (d(i.get("listing")) or date.max, i["name"]))
    upcoming.sort(key=lambda i: d(i["open"]))

    live_html = "".join(live_row(i, gi.get(slug(i["name"])), today) for i in live) or (
        '<tr><td colspan="8" class="loading">No IPO is open or waiting to list right now. See upcoming IPO GMP below.</td></tr>')

    def up_row(i):
        rd = readings_of(gi.get(slug(i["name"])))
        g = (rs(rd[-1][1]) if rd[-1][1] == rd[-1][2] else f"{rs(rd[-1][1])} – {rs(rd[-1][2])}") if rd else '<span class="fl">No quote yet</span>'
        return (f'<tr><td><b class="nm">{esc(i["name"])} IPO</b><span class="tag">{esc(i.get("board") or "")}</span></td>'
                f'<td class="n">{fmt(d(i["open"]))}</td><td class="n">{esc(i.get("band") or "–")}</td><td class="n">{g}</td></tr>')
    up_html = "".join(up_row(i) for i in upcoming) or (
        '<tr><td colspan="4" class="loading">No IPO with announced dates opens in the next 30 days.</td></tr>')

    rr = reality(gmp, by_id)
    rows_html = []
    for ldate, name, said, actual, issue, lopen in rr[:25]:
        gap = said - actual
        if abs(gap) <= CLOSE_PTS:
            vd = '<span class="vd ok">Close</span>'
        elif gap > 0:
            vd = f'<span class="vd hi">GMP too high by {abs(gap):.0f} pts</span>'
        else:
            vd = f'<span class="vd lo">GMP too low by {abs(gap):.0f} pts</span>'
        bar = (f'<div class="bar" title="GMP said {pct(said)}, listed {pct(actual)}">'
               f'<i class="p" style="left:{bar_pos(said):.1f}%"></i><i class="a" style="left:{bar_pos(actual):.1f}%"></i></div>')
        rows_html.append(
            f'<tr><td><b class="nm">{esc(name)}</b><small class="fl">Issue {rs(issue)} · opened {rs(lopen, 2)}</small></td>'
            f'<td class="n">{fmt(ldate)}</td><td class="n">{pct(said)}</td>'
            f'<td class="n"><b class="{"up" if actual >= 0 else "dn"}">{pct(actual)}</b></td><td>{bar}</td><td>{vd}</td></tr>')
    real_html = "".join(rows_html) or (
        '<tr><td colspan="6" class="loading">The scorecard fills in as tracked IPOs list. '
        'Each IPO is added on its listing day.</td></tr>')

    if rr:
        n = len(rr)
        over = sum(1 for r in rr if r[2] - r[3] > CLOSE_PTS)
        close_n = sum(1 for r in rr if abs(r[2] - r[3]) <= CLOSE_PTS)
        miss = sum(abs(r[2] - r[3]) for r in rr) / n
        truth = (f'<div><b>{over} of {n}</b><small>IPOs listed lower than GMP said</small></div>'
                 f'<div><b>{miss:.1f} pts</b><small>average GMP miss</small></div>'
                 f'<div><b>{close_n} of {n}</b><small>listed within 5 pts of GMP</small></div>')
    else:
        truth = ('<div><b>Tracking</b><small>GMP vs real listing for every IPO</small></div>'
                 '<div><b>Daily</b><small>GMP range from several trackers</small></div>'
                 '<div><b>Free</b><small>with the 9AM IPO score</small></div>')

    up = d(gmp.get("updated")) or d(data.get("updated"))
    out = (tpl.replace("<!--N9GM:LIVE-->", live_html).replace("<!--N9GM:UPCOMING-->", up_html)
              .replace("<!--N9GM:REALITY-->", real_html).replace("<!--N9GM:TRUTH-->", truth)
              .replace("<!--N9GM:UPDATED-->", f"GMP updated {fmt(up)}"))
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "gmp-page.html").write_text(out, encoding="utf-8")
    print(f"OK: GMP page rendered with {len(live)} live, {len(upcoming)} upcoming and {len(rr)} reality-check IPOs.")


if __name__ == "__main__":
    main()
