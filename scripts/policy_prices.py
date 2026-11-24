"""Policy Radar price check.

For every policy in policy-radar/policies.json, take the closing price of each
named stock on the last NSE trading day BEFORE the policy date, and the latest
close, and work out the % change. Nifty 50 over the same period is the yardstick.
Writes policy-radar/prices.json, which the Policy Radar page on 9amtraders.com reads.

Prices are NSE bhavcopy closes, which are NOT adjusted for splits or bonuses:
any move bigger than +/-45% is flagged so it can be checked by hand.
"""
import csv
import datetime as dt
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICIES = ROOT / "policy-radar" / "policies.json"
SYMBOLS = ROOT / "policy-radar" / "symbols.json"
OUT = ROOT / "policy-radar" / "prices.json"

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
INDEX_URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{d:%d%m%Y}.csv"
SERIES_RANK = {"EQ": 0, "BE": 1, "BZ": 2, "SM": 3, "ST": 4}
ODD_MOVE = 45.0          # % — bigger moves are probably a split/bonus in unadjusted data
VERDICT_SHARE = 2 / 3    # Rose: 2/3+ of the stocks up AND average up; Fell: 2/3+ down AND average down; else Mixed

_cache = {}


def fetch(url, tries=3):
    req = urllib.request.Request(url, headers=HEADERS)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  HTTP {e.code} on {url} (try {i + 1})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  {e} on {url} (try {i + 1})", file=sys.stderr)
        time.sleep(3 * (i + 1))
    return None


def num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def bhav(d):
    """{symbol: close} for trading day d, or None if there was no trading that day."""
    if d in _cache:
        return _cache[d]
    out = None
    if d.weekday() <= 4:
        raw = fetch(BHAV_URL.format(d=d), tries=2)
        if raw:
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    text = z.open(z.namelist()[0]).read().decode("utf-8-sig", errors="replace")
                best = {}
                for row in csv.DictReader(io.StringIO(text)):
                    sym = (row.get("TckrSymb") or "").strip().upper()
                    ser = (row.get("SctySrs") or "").strip().upper()
                    if ser not in SERIES_RANK:
                        continue
                    px = num(row.get("ClsPric"))
                    if px > 0 and (sym not in best or SERIES_RANK[ser] < best[sym][0]):
                        best[sym] = (SERIES_RANK[ser], px)
                out = {k: round(v[1], 2) for k, v in best.items()} or None
            except zipfile.BadZipFile:
                out = None
    _cache[d] = out
    return out


def nifty(d):
    raw = fetch(INDEX_URL.format(d=d), tries=2)
    if not raw:
        return None
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))):
        if (row.get("Index Name") or "").strip().lower() == "nifty 50":
            v = num(row.get("Closing Index Value"))
            return v or None
    return None


def trading_day_before(d, limit=10):
    """Last trading day strictly before d, with its bhavcopy."""
    for i in range(1, limit + 1):
        day = d - dt.timedelta(days=i)
        b = bhav(day)
        if b:
            return day, b
    return None, None


def latest_trading_day(limit=10):
    today = dt.datetime.now(IST).date()
    for i in range(limit):
        day = today - dt.timedelta(days=i)
        b = bhav(day)
        if b:
            return day, b
    return None, None


def pct(a, b):
    return round((b - a) / a * 100, 2) if a and b else None


def names(s):
    return [x.strip() for x in str(s or "").split(",") if x.strip()]


def main():
    data = json.loads(POLICIES.read_text(encoding="utf-8"))
    symmap = {k: v for k, v in json.loads(SYMBOLS.read_text(encoding="utf-8")).items() if not k.startswith("_")}

    now_day, now_bhav = latest_trading_day()
    if not now_bhav:
        print("Could not get the latest NSE bhavcopy — leaving prices.json as it is.")
        return 1
    now_nifty = nifty(now_day)
    print(f"Latest trading day: {now_day}  Nifty 50: {now_nifty}")

    out = {"updated": dt.datetime.now(IST).date().isoformat(), "as_of": now_day.isoformat(),
           "nifty_now": now_nifty, "unmapped": [], "policies": {}}
    unmapped = set()

    for p in data.get("policies", []):
        try:
            pdate = dt.date.fromisoformat(str(p.get("date", ""))[:10])
        except ValueError:
            continue
        base_day, base_bhav = trading_day_before(pdate)
        if not base_bhav:
            print(f"  no base prices for {p.get('id')} ({pdate})")
            continue
        base_nifty = nifty(base_day)
        rows = []
        for group, field in (("named", "stocks"), ("watch", "also_watch")):
            for name in names(p.get(field)):
                cands = symmap.get(name)
                if not cands:
                    unmapped.add(name)
                    rows.append({"name": name, "group": group, "symbol": None, "note": "no NSE symbol mapped"})
                    continue
                sym = next((s for s in cands if s in now_bhav), None)
                if not sym:
                    rows.append({"name": name, "group": group, "symbol": cands[0], "note": "not found in today's bhavcopy"})
                    continue
                b, n = base_bhav.get(sym), now_bhav.get(sym)
                row = {"name": name, "group": group, "symbol": sym, "before": b, "now": n, "chg": pct(b, n)}
                if b is None:
                    row["note"] = "not listed before the policy date"
                elif row["chg"] is not None and abs(row["chg"]) > ODD_MOVE:
                    row["note"] = "big move: check for a split or bonus"
                rows.append(row)

        def verdict(group):
            ch = [r["chg"] for r in rows if r["group"] == group and r.get("chg") is not None]
            if not ch:
                return None, None, 0, 0
            up = sum(1 for c in ch if c > 0)
            down = sum(1 for c in ch if c < 0)
            avg = round(sum(ch) / len(ch), 2)
            if up >= VERDICT_SHARE * len(ch) and avg > 0:
                v = "Rose"
            elif down >= VERDICT_SHARE * len(ch) and avg < 0:
                v = "Fell"
            else:
                v = "Mixed"
            return v, avg, up, down

        v, avg, up, down = verdict("named")
        basis = "named"
        if v is None:                       # no market-named stocks: judge on the watch list instead
            v, avg, up, down = verdict("watch")
            basis = "watch" if v else None
        nchg = pct(base_nifty, now_nifty)
        out["policies"][p["id"]] = {
            "policy_date": pdate.isoformat(), "base_date": base_day.isoformat(),
            "nifty_before": base_nifty, "nifty_chg": nchg,
            "verdict": v, "basis": basis, "avg_chg": avg, "up": up, "down": down,
            "vs_nifty": round(avg - nchg, 2) if avg is not None and nchg is not None else None,
            "stocks": rows,
        }
        print(f"  {p['id']}: {v} avg {avg}% vs Nifty {nchg}%")

    out["unmapped"] = sorted(unmapped)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT} — {len(out['policies'])} policies; unmapped names: {out['unmapped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
