#!/usr/bin/env python3
"""
Publish the big-investor profile pages to WordPress (same REST login as the GMP and Smart Money pages).

For each file in build/investors/:
  - smart-money.html          -> page with slug "smart-money"
  - <slug>.html               -> child page of "smart-money" with that slug
If a page exists (any status), only its content is replaced, so a published page stays published.
If it does not exist yet, it is created as a DRAFT, so a person can review it before it goes live.
Pages whose content has not changed are skipped.

Needs: WP_URL, WP_USER, WP_APP_PASSWORD (repository secrets). Exits quietly if they are missing.
"""
import base64, json, os, sys, urllib.request, urllib.error, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "build" / "investors"
URL, USER, PWD = (os.environ.get(k, "") for k in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"))
AUTH = "Basic " + base64.b64encode(f"{USER}:{PWD}".encode()).decode()
API = URL.rstrip("/") + "/wp-json/wp/v2/pages"


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": AUTH, "Content-Type": "application/json", "User-Agent": "9am-ipo-data-publisher"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} on {method} {url}: {e.read()[:300]!r}") from None


def find(slug):
    q = urllib.parse.urlencode({"slug": slug, "status": "publish,draft,pending,private", "context": "edit", "per_page": 5})
    got = call("GET", f"{API}?{q}") or []
    return got[0] if got else None


def wrap(html):
    return "<!-- wp:html -->\n" + html + "\n<!-- /wp:html -->"


def title_of(html, fallback):
    for line in html.splitlines()[:6]:
        if "SEO title:" in line:
            return line.split("SEO title:", 1)[1].split("|")[0].strip()
    return fallback


def main():
    if not (URL and USER and PWD):
        print("WordPress secrets are not set, so profile pages were not published (data is still updated).")
        return
    files = sorted(SRC.glob("*.html"))
    if not files:
        print("nothing to publish"); return
    hub_html = (SRC / "smart-money.html").read_text(encoding="utf-8")
    hub = find("smart-money")
    if hub is None:
        hub = call("POST", API, {"title": "Big Investors' Portfolios", "slug": "smart-money", "status": "draft", "content": wrap(hub_html)})
        print(f"created DRAFT smart-money (id {hub['id']})")
    elif (hub.get("content") or {}).get("raw", "").strip() != wrap(hub_html).strip():
        call("POST", f"{API}/{hub['id']}", {"content": wrap(hub_html)})
        print(f"updated smart-money (id {hub['id']}, {hub.get('status')})")
    for f in files:
        slug = f.stem
        if slug == "smart-money":
            continue
        html = f.read_text(encoding="utf-8")
        page = find(slug)
        if page is None:
            new = call("POST", API, {"title": title_of(html, slug.replace("-", " ").title()), "slug": slug, "parent": hub["id"],
                                     "status": "draft", "content": wrap(html)})
            print(f"created DRAFT {slug} (id {new['id']})")
        elif (page.get("content") or {}).get("raw", "").strip() != wrap(html).strip():
            call("POST", f"{API}/{page['id']}", {"content": wrap(html)})
            print(f"updated {slug} (id {page['id']}, {page.get('status')})")
        else:
            print(f"unchanged {slug}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as ex:
        print(ex, file=sys.stderr); sys.exit(1)
