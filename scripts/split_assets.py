#!/usr/bin/env python3
"""
Moves a page template's CSS and JavaScript into their own files served by jsDelivr,
so WordPress can't rewrite them (it turns && into &#038;&#038; and adds </p> tags).

    python scripts/split_assets.py widget/order-wins-page.html order-wins
writes widget/order-wins.css, widget/order-wins.js and rewrites the template so it
loads them from  https://cdn.jsdelivr.net/gh/9amtraders/9am-ipo-data@{{ASSET_VER}}/widget/...
({{ASSET_VER}} is filled in with the commit id by the render scripts).
"""
import re
import sys
from pathlib import Path

CDN = "https://cdn.jsdelivr.net/gh/9amtraders/9am-ipo-data@{{ASSET_VER}}/widget/"


def main(tpl_path, name):
    tpl = Path(tpl_path)
    html = tpl.read_text(encoding="utf-8")
    styles = re.findall(r"<style>(.*?)</style>", html, re.S)
    if styles:
        Path(f"widget/{name}.css").write_text("\n".join(styles), encoding="utf-8")
        first = True

        def sub_style(m):
            nonlocal first
            if first:
                first = False
                return f'<link rel="stylesheet" href="{CDN}{name}.css">'
            return ""
        html = re.sub(r"<style>.*?</style>\n?", sub_style, html, flags=re.S)
    m = re.search(r"<script>\s*\(function\(\)\{.*?\}\)\(\);\s*</script>", html, re.S)
    if m:
        js = m.group(0)[len("<script>"):-len("</script>")]
        Path(f"widget/{name}.js").write_text(js.strip() + "\n", encoding="utf-8")
        html = html[:m.start()] + f'<script src="{CDN}{name}.js" defer></script>' + html[m.end():]
    tpl.write_text(html, encoding="utf-8")
    print(f"{tpl}: css {'moved' if styles else 'none'}, js {'moved' if m else 'NOT FOUND'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
