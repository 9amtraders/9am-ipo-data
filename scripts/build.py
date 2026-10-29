#!/usr/bin/env python3
"""Builds the public data for the 9AM IPO Scan page.

Reads   list.json          the current IPO list (names, dates, price bands)
        raw/<id>.json      research for one IPO: check statuses, findings, sources, metrics
Writes  reports/<id>.json  the scored report the page shows
        ipos.json          the list the page loads, with hasReport and score per IPO

Scores are always computed here from the check statuses, never typed in by hand,
so every IPO is scored the same way.
"""
import json
import math
import re
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = timezone(timedelta(hours=5, minutes=30))
CFG = json.loads((ROOT / "scripts" / "checklist.json").read_text(encoding="utf-8"))
# "na" (not found) counts as neutral, so missing data can never push a score up.
POINTS = {"pass": 1.0, "caution": 0.5, "flag": 0.0, "na": 0.5}
STATUSES = ("pass", "caution", "flag", "na")
errors = []


def slug(name):
    s = re.sub(r"\b(ltd|limited|ipo|pvt|private|the|and)\b", " ", str(name).lower().replace("&", " "))
    return re.sub(r"[^a-z0-9]+", "", s)


def date_or_none(v):
    return v if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else None


def num_or_none(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return round(f, 2) if math.isfinite(f) else None


def text(v, n):
    return re.sub(r"<[^>]+>", "", v).strip()[:n] if isinstance(v, str) else ""


def url_or_empty(v):
    return v if isinstance(v, str) and re.match(r"^https?://[^\s\"'<>]+$", v) else ""


def subscription(v, where):
    """Cleans an IPO's subscription figures and works out a retail investor's allotment chance."""
    if not isinstance(v, dict):
        return None, None
    out = {k: num_or_none(v.get(k)) for k in ("qib", "nii", "retail", "total")}
    for k in ("retailShares", "minAppShares", "retailApps"):
        n = num_or_none(v.get(k))
        out[k] = int(n) if n and n > 0 else None
    out["asOf"] = text(v.get("asOf"), 40)
    out["final"] = bool(v.get("final"))
    out["source"] = url_or_empty(v.get("source"))
    if all(out[k] is None for k in ("qib", "nii", "retail", "total")):
        errors.append(f"{where}: subscription has no figures")
        return None, None
    if not out["source"]:
        errors.append(f"{where}: subscription needs a source URL")
    r = out["retail"]
    if r is None:
        return out, None
    if r <= 1:
        # Retail portion not fully subscribed: every valid application gets what it applied for.
        return out, {"chance": 100.0, "oneIn": 1, "basis": "undersubscribed"}
    if out["retailShares"] and out["minAppShares"] and out["retailApps"]:
        # SEBI lottery: as many applicants as possible get the minimum application, chosen by draw.
        lots = out["retailShares"] // out["minAppShares"]
        c = min(1.0, lots / out["retailApps"])
        basis = "applications"
    else:
        # Without the application count, 1 / times subscribed is the lowest the chance can be.
        c = 1 / r
        basis = "estimate"
    return out, {"chance": round(c * 100, 1), "oneIn": max(1, round(1 / c)), "basis": basis}


def build_report(raw, fname):
    cats = CFG["categories"]
    counts = {s: 0 for s in STATUSES}
    by_cat = {}
    checks = []
    sources = {}
    for s in raw.get("sources") or []:
        u = url_or_empty(s.get("url") if isinstance(s, dict) else None)
        if u:
            sources[u] = text(s.get("title"), 120) or u
    rc = raw.get("checks") or {}
    for cid, cat, label, _rule in CFG["checks"]:
        r = rc.get(cid) or {}
        status = str(r.get("status", "na")).lower()
        if status not in STATUSES:
            errors.append(f"{fname}: check {cid} has bad status {status!r}")
            status = "na"
        finding = text(r.get("finding"), 240) or ("Not found in public sources." if status == "na" else "")
        if status != "na" and not finding:
            errors.append(f"{fname}: check {cid} needs a finding")
        src = url_or_empty(r.get("source"))
        if src:
            sources.setdefault(src, src)
        counts[status] += 1
        b = by_cat.setdefault(cat, {"pts": 0.0, "n": 0, "total": 0, "flags": 0, "pass": 0})
        b["total"] += 1
        b["pts"] += POINTS[status]
        b["n"] += 1
        b["found"] = b.get("found", 0) + (status != "na")
        b["flags"] += status == "flag"
        b["pass"] += status == "pass"
        checks.append({"id": cid, "name": label, "category": cats[cat][0], "status": status, "finding": finding, "source": src})
    missing = set(rc) - {c[0] for c in CFG["checks"]}
    if missing:
        errors.append(f"{fname}: unknown check ids {sorted(missing)}")

    categories, wsum, wtot = [], 0.0, 0
    for key, (cname, weight) in cats.items():
        b = by_cat.get(key, {"pts": 0, "n": 0, "total": 0, "flags": 0, "pass": 0})
        score = round(100 * b["pts"] / b["n"]) if b["n"] else None
        if score is not None:
            wsum += score * weight
            wtot += weight
        found = b.get("found", 0)
        if found:
            detail = f"{b['pass']} of {b['total']} checks passed"
            if b["flags"]:
                detail += f" · {b['flags']} flag" + ("s" if b["flags"] > 1 else "")
            if found < b["total"]:
                detail += f" · {b['total'] - found} not found"
        else:
            detail = "Not found in public sources, scored as neutral"
        categories.append({"name": cname, "score": score, "detail": detail})

    peers = [p for p in (raw.get("peers") or [])[:4] if isinstance(p, dict) and text(p.get("name"), 60)]
    ipo_m = raw.get("ipoMetrics") or {}
    metrics = []
    for key, label, unit, better in CFG["metrics"]:
        vals = [num_or_none((p.get("metrics") or {}).get(key)) for p in peers]
        metrics.append([label, unit, better, num_or_none(ipo_m.get(key)), vals])

    fresh, ofs = num_or_none(raw.get("freshCr")), num_or_none(raw.get("ofsCr"))
    size = num_or_none(raw.get("issueSizeCr"))
    if size is None and fresh is not None:
        size = round(fresh + (ofs or 0), 2)
    total = len(CFG["checks"])
    name = text(raw.get("name"), 80)
    if not name:
        errors.append(f"{fname}: missing name")
    researched = date_or_none(raw.get("researchedOn")) or date.today().isoformat()
    return {
        "id": slug(name),
        "name": name,
        "board": "SME" if str(raw.get("board", "")).upper() == "SME" else "Mainboard",
        "sector": text(raw.get("sector"), 60),
        "exchange": text(raw.get("exchange"), 40),
        "open": date_or_none(raw.get("open")),
        "close": date_or_none(raw.get("close")),
        "listing": date_or_none(raw.get("listing")),
        "band": text(raw.get("priceBand"), 40),
        "issueSizeCr": size,
        "freshCr": fresh,
        "ofsCr": ofs,
        "lotSize": int(raw["lotSize"]) if isinstance(raw.get("lotSize"), (int, float)) else None,
        "summary": text(raw.get("summary"), 900),
        "score": round(wsum / wtot) if wtot else None,
        "counts": counts,
        "totalChecks": total,
        "confidence": "low" if counts["na"] / total > 0.35 else "normal",
        "categories": categories,
        "checks": checks,
        "peers": [text(p["name"], 60) for p in peers],
        "metrics": metrics,
        "sources": [{"url": u, "title": t} for u, t in list(sources.items())[:15]],
        "generatedAt": researched + "T08:00:00+05:30",
    }


def main():
    (ROOT / "reports").mkdir(exist_ok=True)
    lst = json.loads((ROOT / "list.json").read_text(encoding="utf-8"))
    reports = {}
    for f in sorted((ROOT / "raw").glob("*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: invalid JSON ({e})")
            continue
        rep = build_report(raw, f.name)
        if rep["id"]:
            reports[rep["id"]] = rep
            (ROOT / "reports" / f"{rep['id']}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")

    out, seen = [], set()
    for i in lst.get("ipos", []):
        name = text(i.get("name"), 80)
        sid = slug(name)
        if not sid or sid in seen:
            continue
        seen.add(sid)
        rep = reports.get(sid)
        out.append({
            "name": name,
            "aka": [text(a, 60) for a in (i.get("aka") or [])[:8] if text(a, 60)],
            "board": "SME" if str(i.get("board", "")).upper() == "SME" else "Mainboard",
            "open": date_or_none(i.get("open")),
            "close": date_or_none(i.get("close")),
            "listing": date_or_none(i.get("listing")),
            "band": text(i.get("band"), 40),
            "hasReport": bool(rep),
            "score": rep["score"] if rep else None,
        })
        sub, allot = subscription(i.get("sub"), f"list.json {name}")
        if sub:
            out[-1]["sub"] = sub
        if allot:
            out[-1]["allot"] = allot
    # IPOs that dropped off the live list keep their reports, so search still finds them.
    for sid, rep in reports.items():
        if sid not in seen:
            out.append({"name": rep["name"], "aka": [], "board": rep["board"], "open": rep["open"], "close": rep["close"],
                        "listing": rep["listing"], "band": rep["band"], "hasReport": True, "score": rep["score"], "archived": True})

    if errors:
        print("Problems found, nothing written to ipos.json:\n- " + "\n- ".join(errors))
        sys.exit(1)
    updated = date_or_none(lst.get("updated")) or datetime.now(IST).date().isoformat()
    (ROOT / "ipos.json").write_text(json.dumps({"updated": updated, "ipos": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(out)} IPOs in list, {len(reports)} reports.")
    for sid, rep in sorted(reports.items()):
        c = rep["counts"]
        print(f"  {rep['name']}: score {rep['score']} ({c['pass']} pass, {c['caution']} caution, {c['flag']} flag, {c['na']} not found)")
    for i in out:
        if i.get("allot"):
            a = i["allot"]
            print(f"  {i['name']}: retail {i['sub']['retail']}x, allotment chance {a['chance']}% ({a['basis']})")


if __name__ == "__main__":
    main()
