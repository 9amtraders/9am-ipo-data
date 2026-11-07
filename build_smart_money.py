#!/usr/bin/env python3
"""
Smart Money Tracker — nightly data builder for 9amtraders.com
--------------------------------------------------------------
Downloads NSE's free daily Bulk Deals and Block Deals files, merges them into
a rolling ~30-trading-day history, and tags each stock with its industry.

Output: smartmoney/deals.json  (read by the Smart Money Tracker page)
Also stores each deal stock's latest close, so the page can show % moved since the deal.

Put this file in the repo root of 9amtraders/9am-ipo-data.
Educational data only. Not a buy/sell recommendation.
"""
import csv
import io
import zipfile
import re
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import json
import os
import sys
import time
import datetime as dt
import urllib.request
import urllib.error
import http.cookiejar
from pathlib import Path

OUT_FILE = Path(os.environ.get("OUT_FILE", "smartmoney/deals.json"))
KEEP_DAYS = 65                     # ~3 months of trading days kept in the file
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}
BHAV_URL = ("https://nsearchives.nseindia.com/content/cm/"
            "BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip")
BULK_URL = "https://nsearchives.nseindia.com/content/equities/bulk.csv"
BLOCK_URL = "https://nsearchives.nseindia.com/content/equities/block.csv"
SECTOR_URLS = [
    "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
    "https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv",
    "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
]
# NSE JSON API (needs a cookie from the home page) — used only to backfill history
API_HOME = "https://www.nseindia.com/report-detail/display-bulk-and-block-deals"
API_URL = ("https://www.nseindia.com/api/historical/{kind}?"
           "from={f:%d-%m-%Y}&to={t:%d-%m-%Y}")


def fetch(url, tries=4, opener=None):
    req = urllib.request.Request(url, headers=HEADERS)
    op = opener.open if opener else urllib.request.urlopen
    for i in range(tries):
        try:
            with op(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  HTTP {e.code} on {url} (try {i + 1})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  {e} on {url} (try {i + 1})", file=sys.stderr)
        time.sleep(3 * (i + 1))
    return None


def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def num(s):
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def pick(row, *words):
    """Find a column whose name contains all the given words (NSE renames headers)."""
    for k, v in row.items():
        key = (k or "").lower()
        if all(w in key for w in words):
            return v
    return ""


def normalise(row, kind):
    d = parse_date(pick(row, "date"))
    sym = (pick(row, "symbol") or "").strip().upper()
    side = (pick(row, "buy") or "").strip().upper()
    qty = num(pick(row, "quantity"))
    price = num(pick(row, "price"))
    if not (d and sym and side[:1] in "BS" and qty > 0 and price > 0):
        return None
    return {
        "d": d,
        "s": sym,
        "n": (pick(row, "security") or pick(row, "name") or sym).strip(),
        "c": " ".join((pick(row, "client") or "").split()).upper(),
        "b": 1 if side.startswith("B") else 0,
        "q": int(qty),
        "p": round(price, 2),
        "t": kind,
    }


def parse_csv(raw, kind):
    if not raw:
        return []
    text = raw.decode("utf-8-sig", errors="replace")
    if "<html" in text[:300].lower():
        return []
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        r = normalise({(k or "").strip(): v for k, v in row.items()}, kind)
        if r:
            out.append(r)
    return out


def backfill(days=100):
    """Best effort: pull recent history from NSE's JSON API. Silent if blocked."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    if fetch(API_HOME, tries=2, opener=opener) is None:
        return []
    end = dt.datetime.now(IST).date()
    out = []
    for kind, label in (("bulk-deals", "BULK"), ("block-deals", "BLOCK")):
        rows = []
        for back in range(0, days, 30):                 # NSE answers best in ~1-month chunks
            t = end - dt.timedelta(days=back)
            f = max(end - dt.timedelta(days=days), t - dt.timedelta(days=29))
            raw = fetch(API_URL.format(kind=kind, f=f, t=t), tries=2, opener=opener)
            try:
                rows += json.loads(raw or b"{}").get("data", [])
            except ValueError:
                pass
            time.sleep(1)
        for x in rows:
            r = normalise({
                "date": x.get("BD_DT_DATE") or x.get("date"),
                "symbol": x.get("BD_SYMBOL") or x.get("symbol"),
                "security name": x.get("BD_SCRIP_NAME") or x.get("name"),
                "client name": x.get("BD_CLIENT_NAME") or x.get("clientName"),
                "buy/sell": x.get("BD_BUY_SELL") or x.get("buySell"),
                "quantity traded": x.get("BD_QTY_TRD") or x.get("qty"),
                "trade price": x.get("BD_TP_WATP") or x.get("watp"),
            }, label)
            if r:
                out.append(r)
        print(f"  backfill {label}: {len(rows)} rows")
    return out


def load_sectors(old):
    sectors = dict(old)
    for url in SECTOR_URLS:
        raw = fetch(url, tries=2)
        if not raw:
            continue
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))):
            sym = (row.get("Symbol") or "").strip().upper()
            ind = (row.get("Industry") or "").strip()
            if sym and ind:
                sectors[sym] = ind
    return sectors


NEWS_URL = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
NEWS_STOCKS = 30            # headlines for the most-traded deal stocks of the last week
NEWS_PER_STOCK = 3


def clean_name(name, sym):
    n = re.sub(r"\b(limited|ltd\.?|pvt|private|\(india\)|india)\b", " ", name or "", flags=re.I)
    n = re.sub(r"[^A-Za-z0-9& ]+", " ", n)
    n = " ".join(n.split())
    return n if len(n) >= 3 else sym


def fetch_news(deals, dates):
    """Recent Google News headlines for the stocks with the biggest deals (best effort)."""
    recent = set(dates[:5])
    tot, names = {}, {}
    for r in deals:
        if r["d"] in recent:
            tot[r["s"]] = tot.get(r["s"], 0) + r["q"] * r["p"]
            names[r["s"]] = r["n"]
    top = sorted(tot, key=tot.get, reverse=True)[:NEWS_STOCKS]
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10)
    out = {}
    for sym in top:
        q = f'"{clean_name(names[sym], sym)}" share OR stock when:10d'
        raw = fetch(NEWS_URL.format(q=urllib.parse.quote(q)), tries=2)
        time.sleep(1.2)
        if not raw:
            continue
        try:
            items = ET.fromstring(raw).iter("item")
        except ET.ParseError:
            continue
        got = []
        for it in items:
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            src = (it.findtext("source") or "").strip()
            try:
                when = parsedate_to_datetime(it.findtext("pubDate") or "")
            except (TypeError, ValueError):
                continue
            if not (title and link.startswith("http")) or when < cutoff:
                continue
            if src and title.endswith(" - " + src):
                title = title[: -len(src) - 3]
            got.append({"t": title[:160], "u": link, "s": src[:40], "d": when.date().isoformat()})
            if len(got) >= NEWS_PER_STOCK:
                break
        if got:
            out[sym] = got
    print(f"news: headlines for {len(out)} of {len(top)} stocks")
    return out


SERIES_RANK = {"EQ": 0, "BE": 1, "BZ": 2, "SM": 3, "ST": 4}


def latest_closes(symbols):
    """Closing price of each deal stock from the newest NSE bhavcopy (for the 'since deal' %)."""
    day = dt.datetime.now(IST).date()
    for i in range(10):
        d = day - dt.timedelta(days=i)
        if d.weekday() > 4:
            continue
        raw = fetch(BHAV_URL.format(d=d), tries=2)
        if not raw:
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                text = z.open(z.namelist()[0]).read().decode("utf-8-sig", errors="replace")
        except zipfile.BadZipFile:
            continue
        best = {}
        for row in csv.DictReader(io.StringIO(text)):
            sym = (row.get("TckrSymb") or "").strip().upper()
            ser = (row.get("SctySrs") or "").strip().upper()
            if sym not in symbols or ser not in SERIES_RANK:
                continue
            px = num(row.get("ClsPric"))
            if px > 0 and (sym not in best or SERIES_RANK[ser] < best[sym][0]):
                best[sym] = (SERIES_RANK[ser], px)
        if best:
            return d.isoformat(), {k: round(v[1], 2) for k, v in best.items()}
    return None, {}


def main():
    old = {"deals": [], "sectors": {}}
    if OUT_FILE.exists():
        try:
            old = json.loads(OUT_FILE.read_text())
        except ValueError:
            pass

    new = parse_csv(fetch(BULK_URL), "BULK") + parse_csv(fetch(BLOCK_URL), "BLOCK")
    print(f"today's files: {len(new)} deals")
    if len({d['d'] for d in old.get('deals', [])}) < 20:
        new += backfill()

    seen, deals = set(), []
    for r in old.get("deals", []) + new:
        key = (r["d"], r["s"], r["c"], r["b"], r["q"], r["p"], r["t"])
        if key not in seen:
            seen.add(key)
            deals.append(r)

    dates = sorted({r["d"] for r in deals}, reverse=True)[:KEEP_DAYS]
    keep = set(dates)
    deals = [r for r in deals if r["d"] in keep]
    deals.sort(key=lambda r: (r["d"], r["q"] * r["p"]), reverse=True)

    if not deals:
        print("No deals found — keeping old file", file=sys.stderr)
        return

    sectors = load_sectors(old.get("sectors", {}))
    used = {r["s"] for r in deals}
    close_date, closes = latest_closes(used)
    if not closes:                               # keep yesterday's prices if NSE is slow
        close_date, closes = old.get("closeDate"), old.get("close", {})
    news = fetch_news(deals, dates) or old.get("news", {})
    out = {
        "news": {k: v for k, v in news.items() if k in used},
        "updated": dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "closeDate": close_date,
        "close": {k: v for k, v in closes.items() if k in used},
        "source": "NSE bulk & block deals (nseindia.com)",
        "dates": dates,
        "sectors": {s: sectors[s] for s in sorted(used) if s in sectors},
        "deals": deals,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {OUT_FILE}: {len(deals)} deals over {len(dates)} days")


if __name__ == "__main__":
    main()
