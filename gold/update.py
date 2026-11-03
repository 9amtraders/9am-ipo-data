#!/usr/bin/env python3
"""Daily data update for the 9AM Gold Thermometer. Runs in GitHub Actions.

Sources
  today's gold spot price, USD per troy ounce   goldprice.dev (free plan; a visible link is required)
  USD/INR exchange rates                        European Central Bank reference rates, via Frankfurter
  monthly gold prices                           World Bank Commodity Price Data (The Pink Sheet), CC BY 4.0

Writes
  gold/data/monthly.json   monthly average gold price in rupees since 1999
  gold/data/daily.json     one reading per day from launch onwards
  gold/data/latest.json    today's Thermometer reading, used by render.py

If today's price cannot be fetched the script exits with an error and leaves the files
unchanged, so the published pages keep the last good reading.
"""
import io
import json
import os
import re
import statistics
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
IST = timezone(timedelta(hours=5, minutes=30))
OZ_G = 31.1034768  # grams in one troy ounce
UA = "Mozilla/5.0 (compatible; 9am-gold-thermometer/1.0; +https://9amtraders.com)"
HIST_FROM = "2000-01"  # first month whose 12-month average can be built from rupee data
BANDS = [(25, "cheap"), (60, "fair"), (85, "expensive"), (101, "very_expensive")]

WB_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
WB_FALLBACK = [
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx",
]
FX_HOSTS = [
    ("https://api.frankfurter.dev/v1/", "base=USD&symbols=INR"),
    ("https://api.frankfurter.app/", "from=USD&to=INR"),
]


def get(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url, headers=None):
    return json.loads(get(url, headers).decode("utf-8"))


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(name, obj):
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def per_10g(usd_oz, usdinr):
    return usd_oz * usdinr / OZ_G * 10


# ---------- monthly history ----------

def wb_monthly_gold():
    """Monthly average gold price in USD per troy ounce, from the World Bank Pink Sheet."""
    import openpyxl
    urls = []
    try:
        page = get(WB_PAGE).decode("utf-8", "replace")
        urls += re.findall(r'https?://thedocs\.worldbank\.org/[^"\'\s<>]+CMO-Historical-Data-Monthly\.xlsx', page)
    except Exception as e:
        print(f"  World Bank page lookup failed: {e}")
    urls += WB_FALLBACK
    last_err = None
    for url in dict.fromkeys(urls):
        try:
            wb = openpyxl.load_workbook(io.BytesIO(get(url, timeout=120)), read_only=True, data_only=True)
        except Exception as e:
            last_err = e
            print(f"  could not open {url}: {e}")
            continue
        ws = next((wb[n] for n in wb.sheetnames if n.strip().lower() == "monthly prices"), None) or \
            next((wb[n] for n in wb.sheetnames if "monthly" in n.lower()), None)
        if ws is None:
            continue
        col, out = None, {}
        for row in ws.iter_rows(values_only=True):
            if col is None:
                for i, v in enumerate(row):
                    if isinstance(v, str) and v.strip().lower() == "gold":
                        col = i
                        break
                continue
            m = re.fullmatch(r"(\d{4})M(\d{2})", str(row[0] or "").strip())
            if not m or col >= len(row):
                continue
            try:
                v = float(row[col])
            except (TypeError, ValueError):
                continue
            if v > 0:
                out[f"{m.group(1)}-{m.group(2)}"] = v
        if len(out) > 300:
            print(f"  World Bank gold: {len(out)} months, last {max(out)} ({url})")
            return out, url
    raise RuntimeError(f"World Bank monthly gold prices not found ({last_err})")


def fx_series(start, end):
    """Daily USD/INR rates between two dates, from the European Central Bank via Frankfurter."""
    last_err = None
    for host, q in FX_HOSTS:
        try:
            j = get_json(f"{host}{start}..{end}?{q}")
            rates = {d: v["INR"] for d, v in j.get("rates", {}).items() if v.get("INR")}
            if len(rates) > 1000:
                return rates
        except Exception as e:
            last_err = e
            print(f"  FX series from {host} failed: {e}")
    raise RuntimeError(f"USD/INR history not available ({last_err})")


def refresh_monthly(today):
    old = load("monthly.json", None)
    if old and old.get("fetched", "") >= (today - timedelta(days=7)).isoformat():
        return old
    try:
        gold, src = wb_monthly_gold()
        fx = fx_series("1999-01-04", today.isoformat())
    except Exception as e:
        if old:
            print(f"  monthly refresh failed, keeping the saved history: {e}")
            return old
        raise
    fx_m = {}
    for d, v in fx.items():
        fx_m.setdefault(d[:7], []).append(v)
    months = {}
    for m, usd in sorted(gold.items()):
        if m in fx_m:
            r = statistics.fmean(fx_m[m])
            months[m] = {"usd_oz": round(usd, 2), "usdinr": round(r, 4), "inr_10g": round(per_10g(usd, r))}
    out = {"fetched": today.isoformat(), "source": src, "months": months}
    save("monthly.json", out)
    print(f"  monthly history: {len(months)} months, {min(months)} to {max(months)}")
    return out


# ---------- today's price ----------

def spot_usd():
    key = os.environ.get("GOLDPRICE_API_KEY", "").strip()
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    if not key:
        print("  GOLDPRICE_API_KEY not set: using the delayed keyless price")
    j = get_json("https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT", headers)
    s = next(x for x in j["symbols"] if x.get("symbol") == "XAU" and x.get("quote_currency") == "USD")
    return float(s["price"]), s.get("computed_at"), bool(s.get("is_stale"))


def fx_latest():
    last_err = None
    for host, q in FX_HOSTS:
        try:
            j = get_json(f"{host}latest?{q}")
            return float(j["rates"]["INR"]), j.get("date")
        except Exception as e:
            last_err = e
            print(f"  latest FX from {host} failed: {e}")
    raise RuntimeError(f"USD/INR rate not available ({last_err})")


# ---------- the reading ----------

def band_of(pct):
    return next(name for limit, name in BANDS if pct < limit)


def percentile(value, values):
    below = sum(v < value for v in values)
    equal = sum(v == value for v in values)
    return 100 * (below + 0.5 * equal) / len(values)


def main():
    now = datetime.now(IST)
    today = now.date()
    print("Monthly history")
    monthly = refresh_monthly(today)
    print("Today's price")
    usd, computed_at, stale = spot_usd()
    usdinr, fx_date = fx_latest()
    if not (500 < usd < 20000) or not (40 < usdinr < 200):
        sys.exit(f"Price check failed: gold ${usd}/oz, USD/INR {usdinr}. Nothing written.")
    p_today = per_10g(usd, usdinr)
    print(f"  gold ${usd:,.2f}/oz x USD/INR {usdinr} ({fx_date}) = Rs {p_today:,.0f} per 10 g")

    daily = load("daily.json", [])
    daily = [d for d in daily if d["date"] != today.isoformat()]
    daily.append({"date": today.isoformat(), "usd_oz": round(usd, 2), "usdinr": round(usdinr, 4),
                  "fx_date": fx_date, "inr_10g": round(p_today), "source_time": computed_at})
    daily.sort(key=lambda d: d["date"])

    # Monthly series: World Bank months, then months after the World Bank's latest built from our own daily readings.
    series = {m: v["inr_10g"] for m, v in monthly["months"].items()}
    cur_month = today.strftime("%Y-%m")
    by_month = {}
    for d in daily:
        by_month.setdefault(d["date"][:7], []).append(d["inr_10g"])
    for m, vals in by_month.items():
        if m not in series and m < cur_month and len(vals) >= 8:
            series[m] = round(statistics.fmean(vals))
    months = sorted(m for m in series if m < cur_month)
    p = [series[m] for m in months]

    # Stretch: a month's price against the average of the 12 months before it.
    stretch = {}
    for i in range(12, len(months)):
        if months[i] >= HIST_FROM:
            stretch[months[i]] = p[i] / statistics.fmean(p[i - 12:i]) - 1
    hist = list(stretch.values())
    avg12 = statistics.fmean(p[-12:])
    s_now = p_today / avg12 - 1
    pct = percentile(s_now, hist)
    band = band_of(pct)

    # What happened 12 months after past months in the same zone.
    idx = {m: i for i, m in enumerate(months)}
    same, all_fwd = [], []
    for m, s in stretch.items():
        j = idx[m] + 12
        if j >= len(months):
            continue
        fwd = p[j] / p[idx[m]] - 1
        all_fwd.append(fwd)
        if band_of(percentile(s, hist)) == band:
            same.append(fwd)
    pattern = {
        "n": len(same),
        "up_share": round(sum(f > 0 for f in same) / len(same), 4) if same else None,
        "median": round(statistics.median(same), 4) if same else None,
        "base_n": len(all_fwd),
        "base_up_share": round(sum(f > 0 for f in all_fwd) / len(all_fwd), 4),
        "base_median": round(statistics.median(all_fwd), 4),
    }

    # A year ago: today against the average price in the same month last year.
    yoy_month = f"{today.year - 1}-{today.month:02d}"
    yoy = p_today / series[yoy_month] - 1 if yoy_month in series else None

    chart = []
    for i in range(max(12, len(months) - 60), len(months)):
        chart.append({"m": months[i], "p": p[i], "a": round(statistics.fmean(p[i - 12:i]))})

    # The reading for each of the last 60 months, for the colour strip on the page.
    ribbon = []
    for m in sorted(stretch)[-60:]:
        mp = percentile(stretch[m], hist)
        ribbon.append({"m": m, "pct": round(mp, 1), "band": band_of(mp)})

    # Keep today's reading with the daily price, and find the previous day for "change since yesterday".
    daily[-1].update({"pct": round(pct, 1), "band": band})
    prev = next((d for d in reversed(daily[:-1])
                 if (today - date.fromisoformat(d["date"])).days <= 4), None)

    latest = {
        "updated_ist": now.strftime("%Y-%m-%d %H:%M"),
        "date": today.isoformat(),
        "usd_oz": round(usd, 2), "source_time": computed_at, "is_stale": stale,
        "usdinr": round(usdinr, 4), "fx_date": fx_date,
        "inr_10g_24k": round(p_today), "inr_g_24k": round(p_today / 10),
        "inr_10g_22k": round(p_today * 22 / 24), "inr_10g_18k": round(p_today * 18 / 24),
        "avg12": round(avg12), "avg12_from": months[-12], "avg12_to": months[-1],
        "stretch": round(s_now, 4), "percentile": round(pct, 1), "band": band,
        "yoy": round(yoy, 4) if yoy is not None else None, "yoy_month": yoy_month,
        "hist_from": min(stretch), "hist_to": max(stretch), "hist_n": len(hist),
        "pattern": pattern, "chart": chart, "ribbon": ribbon,
        "prev": {"date": prev["date"], "inr_10g": prev["inr_10g"]} if prev else None,
    }
    save("daily.json", daily)
    save("latest.json", latest)
    print(f"Reading: {band}, {s_now:+.1%} vs 12-month average, percentile {pct:.0f} of {len(hist)} months "
          f"({min(stretch)} to {max(stretch)}); past pattern: {pattern}")


if __name__ == "__main__":
    main()
