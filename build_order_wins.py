#!/usr/bin/env python3
"""
Order Wins Tracker — data builder for 9amtraders.com
-----------------------------------------------------
Pulls BSE corporate announcements filed under
"Company Update → Award of Order / Receipt of Order", reads the order value
and client from each filing's summary, and adds:
  * order size in ₹ crore (USD/EUR converted at the day's rate)
  * order size as % of the company's market cap
  * the stock price just before the order and the latest close (for "% since")
  * client type (Govt/PSU, Private, Overseas) and order theme (Defence, Railways…)

Output: orders/orders.json  (read by the Order Wins Tracker page)
Put this file in the repo root of 9amtraders/9am-ipo-data.
Educational data only. Not a buy/sell recommendation.
"""
import csv
import io
import json
import os
import re
import sys
import time
import datetime as dt
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

OUT_FILE = Path(os.environ.get("OUT_FILE", "orders/orders.json"))
KEEP_DAYS = 92                    # ~3 months of orders
FIRST_RUN_DAYS = 92               # backfill on the first run
DAILY_LOOKBACK = 4                # normal runs re-read the last few days (late filings, revisions)
MCAP_REFRESH_DAYS = 7
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bseindia.com/",
    "Origin": "https://www.bseindia.com",
}
ANN_URL = ("https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?"
           "pageno={page}&strCat=Company+Update&strPrevDate={f:%Y%m%d}&strScrip=&strSearch=P"
           "&strToDate={t:%Y%m%d}&strType=C&subcategory=Award+of+Order+%2F+Receipt+of+Order")
PDF_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"
BHAV_URL = ("https://www.bseindia.com/download/BhavCopy/Equity/"
            "BhavCopy_BSE_CM_0_0_0_{d:%Y%m%d}_F_0000.CSV")
MCAP_URL = "https://api.bseindia.com/BseIndiaAPI/api/StockTrading/w?flag=&quotetype=EQ&scripcode={code}"
FX_URL = "https://api.frankfurter.app/latest?from={cur}&to=INR"
FX_FALLBACK = {"USD": 88.0, "EUR": 102.0, "GBP": 117.0}


# ------------------------------------------------------------------ download
# BSE's API only answers browser-like clients that have visited bseindia.com first,
# so we use curl_cffi (Chrome fingerprint) with one warm-up visit. Falls back to urllib.
try:
    from curl_cffi import requests as cffi
except ImportError:            # pip install curl_cffi
    cffi = None
SESSION = None


def session():
    global SESSION
    if SESSION is None and cffi is not None:
        SESSION = cffi.Session(impersonate="chrome")
        try:
            SESSION.get("https://www.bseindia.com/", headers={"Referer": "https://www.google.com/"}, timeout=30)
        except Exception as e:  # noqa: BLE001
            print(f"  BSE warm-up failed: {e}", file=sys.stderr)
    return SESSION


def fetch(url, tries=3, accept_404=True):
    s = session() if "bseindia.com" in url else None
    if s is not None:
        for i in range(tries):
            try:
                r = s.get(url, headers={"Referer": "https://www.bseindia.com/", "Origin": "https://www.bseindia.com"},
                          timeout=40)
                if r.status_code == 200:
                    return r.content
                if r.status_code == 404 and accept_404:
                    return None
                print(f"  HTTP {r.status_code} on {url[:110]} (try {i + 1})", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"  {e} on {url[:110]} (try {i + 1})", file=sys.stderr)
            time.sleep(2 * (i + 1))
        return None
    req = urllib.request.Request(url, headers=HEADERS)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 and accept_404:
                return None
            print(f"  HTTP {e.code} on {url[:110]} (try {i + 1})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  {e} on {url[:110]} (try {i + 1})", file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def get_json(url, tries=3):
    raw = fetch(url, tries)
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8-sig", errors="replace"))
    except ValueError:
        return None


def pick(row, *keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return v
    return ""


# ------------------------------------------------------------------ announcements
def fetch_announcements(start, end):
    out, page, seen = [], 1, set()
    while page <= 80:
        data = get_json(ANN_URL.format(page=page, f=start, t=end))
        rows = (data or {}).get("Table") or []
        new = [r for r in rows if str(r.get("NEWSID")) not in seen]
        if not new:
            break
        seen.update(str(r.get("NEWSID")) for r in new)
        out += new
        if len(rows) < 50:                   # BSE serves 50 rows a page
            break
        page += 1
        time.sleep(0.8)
    print(f"  announcements {start}..{end}: {len(out)} rows")
    return out


def parse_when(s):
    s = str(s or "").strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S",
                "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d %b %Y %H:%M:%S"):
        try:
            return dt.datetime.strptime(s[:26], fmt)
        except ValueError:
            pass
    return None


# ------------------------------------------------------------------ order value
UNIT = {"crore": 1, "crores": 1, "cr": 1, "crs": 1, "lakh": 0.01, "lakhs": 0.01, "lac": 0.01,
        "lacs": 0.01, "million": 0.1, "mn": 0.1, "billion": 100, "bn": 100}
NUM = r"(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
UNITS = r"(?:(crores?|crs?\.?|lakhs?|lacs?|million|mn|billion|bn)\b)"
RX_INR = re.compile(r"(?:rs\.?|inr|₹|rupees|\?)\s*" + NUM + r"\s*(?:/-)?\s*" + UNITS + "?", re.I)
RX_INR_NOCUR = re.compile(NUM + r"\s*" + r"(crores?|crs?\.?|lakhs?|lacs?)\b", re.I)
RX_BARE = re.compile(r"(?:amount(?:ing)?|valued?|worth|value|consideration|price|aggregating|for)\s*(?:of|at|to|approximately|approx\.?|about|:)?\s*"
                     r"(\d{1,3}(?:,\d{2})+,\d{3}(?:\.\d+)?)", re.I)   # e.g. "amount 4,85,35,000"
RX_FX = re.compile(r"(usd|us\s?\$|\$|eur|euro|€|gbp|£)\s*" + NUM + r"\s*" + UNITS + "?", re.I)
RX_FX2 = re.compile(NUM + r"\s*" + r"(million|mn|billion|bn)\s*(usd|us\s?dollars?|dollars?|eur|euros?|gbp)\b", re.I)


def to_num(s):
    return float(s.replace(",", ""))


def fx_code(tok):
    t = tok.lower().replace(" ", "")
    if t in ("eur", "euro", "euros", "€"):
        return "EUR"
    if t in ("gbp", "£"):
        return "GBP"
    return "USD"


def parse_value(text, fx):
    """Return (value in ₹ crore, raw text, currency) — the largest amount mentioned."""
    best = (0.0, "", "INR")
    t = " ".join(str(text or "").split())
    for m in RX_INR.finditer(t):
        n, unit = to_num(m.group(1)), (m.group(2) or "").lower().rstrip(".")
        cr = n * UNIT[unit] if unit else n / 1e7          # bare rupees
        if cr > best[0]:
            best = (cr, m.group(0), "INR")
    for m in RX_INR_NOCUR.finditer(t):
        cr = to_num(m.group(1)) * UNIT[m.group(2).lower().rstrip(".")]
        if cr > best[0]:
            best = (cr, m.group(0), "INR")
    for m in RX_BARE.finditer(t):
        cr = to_num(m.group(1)) / 1e7
        if cr > best[0]:
            best = (cr, m.group(0)[-30:], "INR")
    for m in RX_FX.finditer(t):
        cur, n, unit = fx_code(m.group(1)), to_num(m.group(2)), (m.group(3) or "").lower()
        amt = n * {"million": 1e6, "mn": 1e6, "billion": 1e9, "bn": 1e9}.get(unit, 1)
        cr = amt * fx[cur] / 1e7
        if cr > best[0]:
            best = (cr, m.group(0), cur)
    for m in RX_FX2.finditer(t):
        cur = fx_code(re.sub(r"s$", "", m.group(3).lower().replace("us", "").replace("dollar", "usd")) or "usd")
        amt = to_num(m.group(1)) * (1e9 if m.group(2).lower() in ("billion", "bn") else 1e6)
        cr = amt * fx[cur] / 1e7
        if cr > best[0]:
            best = (cr, m.group(0), cur)
    if best[0] > 500000:            # > ₹5 lakh crore is almost surely a parsing slip
        return 0.0, "", "INR"
    return round(best[0], 2), best[1][:60], best[2]


# ------------------------------------------------------------------ client & theme
RX_CLIENT = re.compile(
    r"\b(?:from|by|with)\s+(?:m/s\.?\s*)?((?:the\s+)?[A-Z][\w&.,'()\-/ ]{2,90}?)"
    r"(?=\s+(?:for|worth|woth|valued|valuing|amounting|aggregating|of\s+(?:rs|inr|₹|usd)|to\s+(?:supply|execute|provide|the)|towards|under|in\s+(?:respect|association)|amounting|dated|vide)\b|[.;:]|\s*\(|$)")
GOVT = re.compile(r"\b(government of|govt\.? of|undertaking|port authority|port trust|devaswom|board\b|vij company|commission\b|department|tamil ?nadu|kerala|karnataka|maharashtra|gujarat|rajasthan|uttar pradesh|madhya pradesh|telangana|andhra|odisha|bihar|west bengal|haryana|punjab|assam|grse|garden reach|national highways|authority of india|of india\b|ministry|govt|government|nhai|nhidcl|indian railways?|railway|rvnl|ircon|dfccil|rites|"
                  r"ntpc|nhpc|sjvn|powergrid|power grid|pgcil|bhel|bel\b|bharat electronics|hal\b|hindustan aeronautics|"
                  r"drdo|indian (army|navy|air force)|mod\b|defence|ongc|iocl|indian oil|bpcl|hpcl|gail|oil india|"
                  r"coal india|nmdc|sail|nlc|mahanadi|bccl|secl|ncl\b|wcl\b|state|municipal|corporation of|nagar|"
                  r"development authority|jal|nigam|vidyut|discom|transco|genco|seb\b|psu|public works|pwd|"
                  r"cpwd|nbcc|npcil|isro|bsnl|mtnl|airports authority|aai\b|metro rail|smart city|"
                  r"public sector|central|union|cochin shipyard|mazagon|grse|bdl\b|bharat dynamics|indian oil)", re.I)
OVERSEAS = re.compile(r"\b(overseas|export|international (order|client|customer|market)|middle east|africa|europe|usa|u\.s\.|uk\b|gcc|"
                      r"saudi|uae|dubai|qatar|oman|kuwait|bangladesh|nepal|sri lanka|kenya|nigeria|germany|"
                      r"japan|singapore|australia|canada|brazil|mexico|foreign)\b", re.I)
THEMES = [
    ("Healthcare", r"hospital|pharma|medical|health|drug|vaccine|diagnostic|patient|monitor type|ventilator"),
    ("Defence", r"defen[cs]e|army|navy|air force|missile|radar|ammunition|drdo|military|armou?r|warship|bel\b|hal\b"),
    ("Railways", r"rail|metro|coach|wagon|locomotive|vande|rvnl|ircon|dfccil|kavach|signalling|track"),
    ("Power & Renewables", r"solar|wind|power|renewable|transmission|substation|transformer|epc.*mw|\bmw\b|\bgw\b|electri|battery|bess|discom|smart meter"),
    ("Roads & Infra", r"road|highway|nhai|bridge|tunnel|flyover|expressway|infra|construction|civil|building|airport|port\b|jetty"),
    ("Water", r"water|irrigation|sewage|pipeline|jal|drinking|canal|desalination"),
    ("Oil, Gas & Mining", r"oil|gas|ongc|refiner|mining|coal|mineral|drilling|lng|cgd"),
    ("IT & Telecom", r"software|it services|digital|cloud|data cent|telecom|5g|network|fibre|fiber|cyber|ai\b|saas"),
    ("Ships & Engineering", r"ship|vessel|boat|engineering|machine|equipment|valve|pump|boiler|turbine|crane"),
]


NOT_ORDER = re.compile(r"\b(income[- ]tax|gst|cgst|sgst|igst|goods and services tax|customs|excise|tax demand|demand order|"
                       r"assessment|rectification|appellate|appeal|tribunal|nclt|nclat|high court|supreme court|court|"
                       r"penalty|show[- ]cause|adjudicat|commissioner|regulatory action|actions? taken|order passed|"
                       r"sebi order|settlement order|interim order|winding up|arbitration award|attachment)\b", re.I)
IS_ORDER = re.compile(r"\b(work order|purchase order|letter of (award|intent)|loa\b|loi\b|contract|tender|l-?1|"
                      r"supply order|service order|new orders?|orders? (worth|valued|of rs)|bagged|secured|won)\b", re.I)


def not_business_order(text):
    return bool(NOT_ORDER.search(text or "")) and not IS_ORDER.search(text or "")


def pdf_text(url):
    """Text of the first pages of a filing PDF (best effort; needs pypdf)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    raw = fetch(url, tries=2)
    if not raw or not raw[:5] == b"%PDF-":
        return ""
    try:
        rd = PdfReader(io.BytesIO(raw))
        txt = " ".join((pg.extract_text() or "") for pg in rd.pages[:3])
    except Exception:  # noqa: BLE001
        return ""
    return " ".join(txt.split())[:8000]


RX_CTX = re.compile(r"(order|contract|award|worth|valued|value|amount|consideration|aggregat|lo[ai]\b)", re.I)
RX_SKIP = re.compile(r"(?i)order ?book|backlog|order inflow|unexecuted|cumulative|year[- ]to[- ]date|ytd|"
                     r"so far|total orders|capital|turnover|net worth|revenue|market (size|opportunity)|classif|"
                     r"authori[sz]ed|range of|between rs|crore to|cr to")
PDF_VER = 3


def value_from_pdf(text, fx):
    """First amount in a sentence about the order; skips order-book totals, share capital, size bands."""
    for sent in re.split(r"(?<=[.;!?])\s+(?=[A-Z₹*(\"'])", text):
        if len(sent) > 400:
            sent = sent[:400]
        if not RX_CTX.search(sent) or RX_SKIP.search(sent):
            continue
        v = parse_value(sent, fx)
        if v[0] > 0:
            return v
    return 0.0, "", "INR"


def client_of(text):
    m = RX_CLIENT.search(" ".join(str(text or "").split()))
    if not m:
        return ""
    c = re.sub(r"(?i)^m/s\.?\s*", "", m.group(1).strip(" ,.-"))
    c = re.sub(r"\b(?:an?|the)\s+(?=order|contract)\b", "", c, flags=re.I)
    if len(c) < 3 or re.match(r"(?i)(the\s+)?(company|board|exchange|us|its|their|stock exchange)\b", c):
        return ""
    return c[:80]


def client_type(client, text, cur, name=""):
    if name:
        text = re.sub(re.escape(name), " ", text or "", flags=re.I)
    blob = f"{client} {text}"
    if GOVT.search(client or "") or (not client and GOVT.search(text or "")):
        return "govt"
    if cur != "INR" or OVERSEAS.search(blob):
        return "overseas"
    return "private"


def theme_of(text):
    for name, rx in THEMES:
        if re.search(rx, text or "", re.I):
            return name
    return "Other"


# ------------------------------------------------------------------ prices & market cap
_bhav_cache = {}


def bhav(day):
    """{scrip code: (symbol, close)} from the BSE bhavcopy of that day, or None."""
    if day in _bhav_cache:
        return _bhav_cache[day]
    raw = fetch(BHAV_URL.format(d=day), tries=2)
    res = None
    if raw and b"," in raw[:200]:
        res = {}
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))):
            code = (row.get("FinInstrmId") or "").strip()
            try:
                px = float(row.get("ClsPric") or 0)
            except ValueError:
                continue
            if code and px > 0:
                res[code] = ((row.get("TckrSymb") or "").strip(), px)
    _bhav_cache[day] = res
    return res


def close_before(day, limit=8):
    """Bhavcopy of the last trading day strictly before `day`."""
    d = day - dt.timedelta(days=1)
    for _ in range(limit):
        if d.weekday() < 5:
            b = bhav(d)
            if b:
                return d, b
        d -= dt.timedelta(days=1)
    return None, {}


def latest_bhav():
    d = dt.datetime.now(IST).date()
    for _ in range(10):
        if d.weekday() < 5:
            b = bhav(d)
            if b:
                return d, b
        d -= dt.timedelta(days=1)
    return None, {}


def market_cap(code):
    data = get_json(MCAP_URL.format(code=code), tries=2)
    if not isinstance(data, dict):
        return None
    for k in ("MktCapFull", "MktCapFF", "mktcap", "MarketCap"):
        v = data.get(k)
        try:
            v = float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if v > 0:
            return round(v, 2)
    return None


def fx_rates(old):
    rates = dict(FX_FALLBACK)
    rates.update(old or {})
    for cur in ("USD", "EUR", "GBP"):
        data = get_json(FX_URL.format(cur=cur), tries=2)
        try:
            rates[cur] = round(float(data["rates"]["INR"]), 2)
        except (TypeError, KeyError, ValueError):
            pass
    return rates


# ------------------------------------------------------------------ main
def main():
    old = {"orders": []}
    if OUT_FILE.exists():
        try:
            old = json.loads(OUT_FILE.read_text())
        except ValueError:
            pass
    known = {o["id"]: o for o in old.get("orders", [])}
    try:
        for k, v in json.loads(Path("orders/pdfcache.json").read_text()).items():
            if k in known:
                known[k].update(v)
    except (OSError, ValueError):
        pass
    today = dt.datetime.now(IST).date()
    first = len(known) < 200 or any(o.get("pdf") not in (None, PDF_VER) for o in known.values())
    start = today - dt.timedelta(days=FIRST_RUN_DAYS if first else DAILY_LOOKBACK)
    fx = fx_rates(old.get("fx"))

    rows = []
    s = start
    while s <= today:                          # month-sized windows are kinder to the BSE API
        e = min(today, s + dt.timedelta(days=30))
        rows += fetch_announcements(s, e)
        s = e + dt.timedelta(days=1)

    added = 0
    for r in rows:
        nid = str(pick(r, "NEWSID", "NewsId", "NEWS_ID")).strip()
        code = str(pick(r, "SCRIP_CD", "ScripCode", "SCRIPCODE")).strip()
        when = parse_when(pick(r, "NEWS_DT", "DT_TM", "News_submission_dt", "DissemDT"))
        if not (nid and code and when):
            continue
        head = " ".join(str(pick(r, "HEADLINE", "NEWSSUB")).split())
        more = " ".join(str(pick(r, "MORE")).split())
        if "Announcement under Regulation 30 (LODR)-" in more:   # just the filing's title
            more = ""
        text = f"{head} {more}"
        att = str(pick(r, "ATTACHMENTNAME")).strip()
        o = known.get(nid, {})
        v, vr, cur = parse_value(text, fx)
        cl = client_of(more) or client_of(head)
        url = ((PDF_URL if int(r.get("PDFFLAG") or 0) != 2 else PDF_HIST_URL).format(att)) if att else ""
        if url and (not v or not cl) and o.get("pdf") != PDF_VER:
            o["pdf"] = PDF_VER                                 # read each PDF once per parser version
            o.pop("vp", None)
            pt = pdf_text(url)
            if pt:
                o["pt"] = pt[:2500]
                if not v:
                    v, vr, cur = value_from_pdf(pt, fx)
                    o["vp"] = 1 if v else 0
                if not cl:
                    cl = client_of(pt[:3000])
        elif o.get("pdf") == PDF_VER and not v and o.get("v"):
            v, vr, cur, cl = o["v"], o.get("vr", ""), o.get("cur", "INR"), cl or o.get("cl", "")
        if not_business_order(f"{text} {o.get('pt', '')[:600]}"):
            known.pop(nid, None)
            continue
        o.update({
            "id": nid, "c": code,
            "n": " ".join(str(pick(r, "SLONGNAME", "LONG_NAME", "COMPANYNAME")).split()) or code,
            "d": when.date().isoformat(), "tm": when.strftime("%H:%M"),
            "h": head[:300], "m": more[:600],
            "u": url,
            "v": v, "vr": vr, "cur": cur, "cl": cl,
            "ct": client_type(cl, f"{text} {o.get('pt', '')[:800]}", cur, str(pick(r, "SLONGNAME"))),
            "th": theme_of(f"{text} {o.get('pt', '')[:800]}"),
        })
        if nid not in known:
            added += 1
        known[nid] = o

    cutoff = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    orders = [o for o in known.values() if o["d"] >= cutoff]

    # same company, same value, same day = a re-filed duplicate
    seen, uniq = set(), []
    for o in sorted(orders, key=lambda o: (o["d"], o.get("tm", "")), reverse=True):
        key = (o["c"], o["d"], o["v"]) if o["v"] else (o["c"], o["d"], "noval")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(o)
    orders = uniq

    # price before each order (set once) + latest close
    for o in orders:
        if "p0" not in o:
            day, b = close_before(dt.date.fromisoformat(o["d"]))
            if b and o["c"] in b:
                o["s"], o["p0"] = b[o["c"]][0], b[o["c"]][1]
    close_date, lb = latest_bhav()
    codes = {o["c"] for o in orders}
    close = {c: lb[c][1] for c in codes if c in lb} if lb else old.get("close", {})
    for o in orders:
        if not o.get("s") and lb and o["c"] in lb:
            o["s"] = lb[o["c"]][0]

    # market cap, refreshed weekly per company
    mcap = old.get("mcap", {})
    mdate = old.get("mcapDate", {})
    for c in sorted(codes):
        last = mdate.get(c)
        if last and (today - dt.date.fromisoformat(last)).days < MCAP_REFRESH_DAYS:
            continue
        v = market_cap(c)
        if v:
            mcap[c], mdate[c] = v, today.isoformat()
        time.sleep(0.4)

    # a value read from a PDF that is bigger than 2x the whole company is almost surely a misread
    for o in orders:
        m = mcap.get(o["c"])
        if o.get("vp") and m and o["v"] > 2 * m:
            o["v"], o["vr"], o["chk"] = 0.0, "", 1

    out = {
        "updated": dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "source": "BSE corporate announcements — Award of Order / Receipt of Order",
        "fx": fx,
        "closeDate": close_date.isoformat() if close_date else old.get("closeDate"),
        "close": close,
        "mcap": {c: mcap[c] for c in codes if c in mcap},
        "mcapDate": {c: mdate[c] for c in codes if c in mdate},
        "orders": sorted(orders, key=lambda o: (o["d"], o.get("tm", "")), reverse=True),
    }
    state = {o["id"]: {k: o[k] for k in ("pdf", "pt", "vp") if k in o} for o in orders}
    Path("orders/pdfcache.json").parent.mkdir(parents=True, exist_ok=True)
    Path("orders/pdfcache.json").write_text(json.dumps(state, separators=(",", ":"), ensure_ascii=False))
    out = {**out, "orders": [{k: v for k, v in o.items() if k not in ("pdf", "pt", "vp")} for o in out["orders"]],
    }
    if not out["orders"]:
        print("No orders found — keeping old file", file=sys.stderr)
        return
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    valued = sum(1 for o in out["orders"] if o["v"])
    print(f"wrote {OUT_FILE}: {len(out['orders'])} orders ({added} new, {valued} with a value), "
          f"{len(out['mcap'])} market caps, closes for {len(close)}")


if __name__ == "__main__":
    main()
