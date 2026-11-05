#!/usr/bin/env python3
"""
Bubble Phase Meter — nightly data builder for 9amtraders.com
-------------------------------------------------------------
Reads free NSE equity bhavcopies, keeps ~16 months of daily prices for the
Nifty 500, and sorts every stock into one phase of the bubble cycle:

    Stealth  ->  Awareness  ->  Mania  ->  Blow-off

Output: bubble/phases.json  (read by the page on 9amtraders.com)

Price-pattern classification only. Not a buy/sell recommendation.
Concept: Dr. Jean-Paul Rodrigue's "Stages in a bubble".
"""
import io
import json
import os
import sys
import time
import zipfile
import datetime as dt
import urllib.request
import urllib.error
from pathlib import Path

import numpy as np
import pandas as pd

OUT_FILE = Path(os.environ.get("OUT_FILE", "bubble/phases.json"))
TEMP_FILE = OUT_FILE.with_name("temperature.json")   # market temperature history
STATE_FILE = OUT_FILE.with_name("state.json")        # each stock's confirmed phase
HIST_FILE = Path(os.environ.get("HIST_FILE", ".cache/bubble_history.csv.gz"))
KEEP_CALENDAR_DAYS = 780          # ~530 trading days: stable 200 EMA + 1 year of replay
REPLAY_DAYS = 260                 # first run rebuilds ~1 year of phase history
CONFIRM_DAYS = 2                  # days a new phase must hold before it counts
MIN_ROWS = 210                    # skip stocks listed too recently
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}
BHAV_URL = ("https://nsearchives.nseindia.com/content/cm/"
            "BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip")
NIFTY500_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
FNO_URL = "https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv"


# ---------------------------------------------------------------- download
def fetch(url, tries=4):
    req = urllib.request.Request(url, headers=HEADERS)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:          # holiday / not published yet
                return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def load_bhav(day):
    raw = fetch(BHAV_URL.format(d=day))
    if not raw:
        return None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]))
    df = df[df["SctySrs"].isin(["EQ", "BE", "BZ"])]
    return pd.DataFrame({
        "date": pd.to_datetime(df["TradDt"]).dt.strftime("%Y-%m-%d"),
        "sym": df["TckrSymb"].str.strip(),
        "high": df["HghPric"].astype(float),
        "low": df["LwPric"].astype(float),
        "close": df["ClsPric"].astype(float),
        "vol": df["TtlTradgVol"].astype(float),
    })


def load_universe():
    raw = fetch(NIFTY500_URL)
    if not raw:
        sys.exit("Could not download the Nifty 500 list from NSE.")
    n500 = pd.read_csv(io.BytesIO(raw))
    n500.columns = [c.strip() for c in n500.columns]
    uni = {r["Symbol"].strip(): {"name": r["Company Name"].strip(),
                                  "sector": r["Industry"].strip()}
           for _, r in n500.iterrows()}
    fno = set()
    raw = fetch(FNO_URL)
    if raw:
        for line in raw.decode("utf-8", "ignore").splitlines()[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) > 1 and parts[1] and parts[1] != "Symbol":
                fno.add(parts[1])
    return uni, fno


def update_history(today):
    if HIST_FILE.exists():
        hist = pd.read_csv(HIST_FILE)
        start = dt.date.fromisoformat(hist["date"].max()) + dt.timedelta(days=1)
    else:
        hist = pd.DataFrame(columns=["date", "sym", "high", "low", "close", "vol"])
        start = today - dt.timedelta(days=KEEP_CALENDAR_DAYS)
        print(f"No history found: back-filling from {start} (takes a few minutes)")

    frames, d = [hist], start
    while d <= today:
        if d.weekday() < 5:
            day = load_bhav(d)
            if day is not None:
                frames.append(day)
                print("  got", d)
            time.sleep(0.6)            # be polite to NSE
        d += dt.timedelta(days=1)

    hist = pd.concat(frames, ignore_index=True)
    hist = hist.drop_duplicates(["date", "sym"], keep="last")
    cutoff = (today - dt.timedelta(days=KEEP_CALENDAR_DAYS)).isoformat()
    hist = hist[hist["date"] >= cutoff]
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    hist.to_csv(HIST_FILE, index=False, compression="gzip")
    return hist



# ---------------------------------------------------------------- maths
def adjust_splits(g):
    """Bhavcopy prices are unadjusted. A one-day fall of more than 45% is
    almost always a split/bonus (circuit limits stop real falls that big),
    so earlier prices are scaled down to match."""
    g = g.copy()
    ratio = g["close"] / g["close"].shift(1)
    for idx in g.index[ratio < 0.55]:
        f = ratio.loc[idx]
        before = g.index < idx
        g.loc[before, ["high", "low", "close"]] *= f
        g.loc[before, "vol"] /= f
    return g


def rsi(series, n=14):
    delta = series.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def indicators(g):
    """All metrics for every trading day of one stock (only days with enough
    history are returned). Each row uses only data up to that day."""
    g = adjust_splits(g.sort_values("date").reset_index(drop=True))
    c, h, l, v = g["close"], g["high"], g["low"], g["vol"]
    e200 = c.ewm(span=200, adjust=False).mean()
    e50 = c.ewm(span=50, adjust=False).mean()
    d200 = c / e200 - 1
    f = pd.DataFrame({"date": g["date"], "close": c.round(2), "d200": d200})
    f["slope"] = e200 / e200.shift(20) - 1                       # 200 EMA slope, 1 month
    f["peak"] = d200.rolling(120, min_periods=1).max()            # max stretch, 6 months
    f["dd"] = c / h.rolling(250, min_periods=1).max() - 1         # from 52-week high
    f["up"] = c / l.rolling(250, min_periods=1).min() - 1         # from 52-week low
    f["rsi"] = rsi(c)
    f["below50"] = c < e50
    f["rng60"] = h.rolling(60, min_periods=1).max() / l.rolling(60, min_periods=1).min() - 1
    f["vr"] = v.rolling(10, min_periods=1).mean() / v.rolling(100, min_periods=1).mean().clip(lower=1)
    f["chg1d"] = c.pct_change()
    f["chg1m"] = c / c.shift(21) - 1
    return f.iloc[MIN_ROWS - 1:]


def metrics(g):
    """Latest day's metrics as a dict."""
    return indicators(g).iloc[-1].to_dict()


def pct(x):
    return f"{x * 100:+.0f}%"


def classify(m):
    """Returns (phase, stage, reasons) or (None, None, []) when the stock
    is not in a clear cycle phase (e.g. a long, slow downtrend)."""
    d, dd, slope, r, peak = m["d200"], m["dd"], m["slope"], m["rsi"], m["peak"]

    # 1. Blow-off: had a mania-sized run in the last 6 months, now well off the top
    if peak >= 0.35 and dd <= -0.25 and m["below50"]:
        if dd > -0.35 and d > 0:
            stage = "Denial"
        elif dd > -0.50:
            stage = "Fear"
        elif r < 35:
            stage = "Despair"
        else:
            stage = "Capitulation"
        return "blowoff", stage, [
            f"Was stretched up to {pct(peak)} above its 200-day average in the last 6 months",
            f"Now {pct(dd)} from its 52-week high",
            "Closed below its 50-day average",
        ]

    # 2. Mania: far above the long-term average and still near the top
    if d >= 0.35 and dd >= -0.15:
        stage = "Enthusiasm" if d < 0.60 else ("Greed" if d < 1.00 else "Delusion")
        why = [f"Trading {pct(d)} above its 200-day average",
               f"Only {pct(dd)} from its 52-week high"]
        if r >= 70:
            why.append(f"RSI is {r:.0f} (overheated above 70)")
        if m["vr"] >= 1.5:
            why.append(f"Volume is {m['vr']:.1f}x its normal level")
        return "mania", stage, why

    # 3. Awareness: steady uptrend above a rising 200 EMA
    if d > 0.03 and slope > 0.005:
        if dd <= -0.10:
            stage = "Bear trap"
        elif d < 0.12:
            stage = "Take off"
        elif d >= 0.25:
            stage = "Media attention"
        else:
            stage = "Steady climb"
        return "awareness", stage, [
            f"{pct(d)} above a rising 200-day average",
            f"{pct(m['up'])} up from its 52-week low",
            f"{pct(dd)} from its 52-week high",
        ]

    # 4. Stealth: flat, quiet base hugging the 200 EMA
    if abs(d) <= 0.08 and abs(slope) <= 0.02 and m["rng60"] <= 0.30:
        return "stealth", "Quiet base", [
            f"Within {abs(d) * 100:.0f}% of a flat 200-day average",
            f"Moved in a {m['rng60'] * 100:.0f}% range over 3 months",
            f"Volume is {m['vr']:.1f}x normal",
        ]

    return None, None, []


# ---------------------------------------------------------------- phase memory
def step(e, date, raw, stage, why):
    """Advance one stock's confirmed phase by one trading day.
    A new phase only counts once it shows up CONFIRM_DAYS days in a row,
    so stocks sitting on a boundary don't flip back and forth."""
    raw = raw or "none"
    if e is None:
        return {"p": raw, "st": stage, "why": why, "since": date, "days": 1,
                "known": False, "pend": None, "pc": 0, "was": None, "moved": None}
    e["days"] += 1
    if raw == e["p"]:
        e.update(st=stage, why=why, pend=None, pc=0)
    else:
        e["pc"] = e["pc"] + 1 if e["pend"] == raw else 1
        e["pend"] = raw
        if e["pc"] >= CONFIRM_DAYS:
            e.update(was=e["p"], p=raw, st=stage, why=why, since=date, days=1,
                     known=True, pend=None, pc=0, moved=date)
    return e


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default


# ---------------------------------------------------------------- main
def main():
    now = dt.datetime.now(IST)
    hist = update_history(now.date())
    universe, fno = load_universe()
    hist = hist[hist["sym"].isin(universe)]
    if hist.empty:
        sys.exit("No price history - check the NSE downloads.")
    all_dates = sorted(hist["date"].unique())
    data_date = all_dates[-1]

    state = load_json(STATE_FILE, {})
    smap = state.get("stocks", {})
    last = state.get("last")
    if last:
        todo = [d for d in all_dates if d > last]
    else:
        todo = all_dates[-REPLAY_DAYS:]
        print(f"First run: replaying {len(todo)} trading days to build phase history")
    todo_set = set(todo)

    temp = {d: {"t": 0, "stealth": 0, "awareness": 0, "mania": 0, "blowoff": 0} for d in todo}
    latest = {}
    for sym, g in hist.groupby("sym"):
        f = indicators(g)
        if f.empty:
            continue
        e = smap.get(sym)
        for row in f[f["date"].isin(todo_set)].to_dict("records"):
            phase, stage, why = classify(row)
            e = step(e, row["date"], phase, stage, why)
            t = temp[row["date"]]
            t["t"] += 1
            if e["p"] in t:
                t[e["p"]] += 1
        if e is not None:
            smap[sym] = e
        if f["date"].iloc[-1] == data_date:
            latest[sym] = f.iloc[-1].to_dict()

    # drop stocks that left the index or stopped trading
    smap = {s: e for s, e in smap.items() if s in latest}

    stocks = []
    for sym, m in latest.items():
        e = smap[sym]
        if e["p"] == "none":
            continue
        info = universe[sym]
        stocks.append({
            "s": sym, "n": info["name"], "sec": info["sector"], "fno": sym in fno,
            "p": e["p"], "st": e["st"], "why": e["why"],
            "was": e["was"] if e["moved"] == data_date and e["was"] != "none" else None,
            "days": e["days"], "known": e["known"], "since": e["since"],
            "pend": e["pend"] if e["pc"] else None,
            "c": round(float(m["close"]), 2), "d200": round(m["d200"] * 100, 1),
            "dd": round(m["dd"] * 100, 1), "rsi": round(m["rsi"]),
            "vr": round(m["vr"], 2), "d1": round(m["chg1d"] * 100, 2),
            "m1": round(m["chg1m"] * 100, 1),
        })

    counts = {k: sum(1 for s in stocks if s["p"] == k)
              for k in ("stealth", "awareness", "mania", "blowoff")}
    out = {
        "date": data_date,
        "built": now.strftime("%Y-%m-%d %H:%M IST"),
        "universe": "Nifty 500",
        "confirm_days": CONFIRM_DAYS,
        "total": len(latest),
        "counts": counts,
        "unclassified": len(latest) - len(stocks),
        "stocks": sorted(stocks, key=lambda s: -abs(s["d200"])),
    }

    # market temperature history: one row per trading day
    th = load_json(TEMP_FILE, {"days": []})
    rows = {r["d"]: r for r in th.get("days", [])}
    for d, t in temp.items():
        if t["t"]:
            rows[d] = {"d": d, "t": t["t"], "st": t["stealth"], "aw": t["awareness"],
                       "ma": t["mania"], "bo": t["blowoff"]}
    th = {"universe": "Nifty 500", "days": [rows[d] for d in sorted(rows)][-1300:]}

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    TEMP_FILE.write_text(json.dumps(th, separators=(",", ":")))
    STATE_FILE.write_text(json.dumps({"last": data_date, "stocks": smap}, separators=(",", ":")))
    print(f"{data_date}: {counts}, unclassified {out['unclassified']}, "
          f"temperature days {len(th['days'])}")


if __name__ == "__main__":
    main()
