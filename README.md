# 9am-ipo-data

Data behind the free IPO Analyzer on [9amtraders.com](https://9amtraders.com/ipo-analyzer-india/).

- `ipos.json` — current Indian IPOs, loaded by the page
- `reports/` — one scored report per IPO
- `raw/` — the research each report is built from
- `scripts/checklist.json` — the 33 checks and their rules
- `scripts/build.py` — computes every score from the checks
- `TASK.md` — what the daily update does
- `widget/allotment-page.html` + `scripts/render_allotment.py` — the IPO Allotment Status page; `.github/workflows/allotment-page.yml` publishes it to WordPress after each update

Reports are built from public sources and may contain errors. They are educational and not a recommendation to apply for, buy or sell any security.
- `gold/` — the Gold Thermometer (`update.py` fetches prices, `render.py` builds the English and Hindi pages); `.github/workflows/gold-thermometer.yml` runs it daily and refreshes the two WordPress pages
- `gmp.json` + `widget/gmp-page.html` + `scripts/render_gmp.py` — the IPO GMP Today page with the GMP Reality Check (GMP before listing vs actual listing); `.github/workflows/gmp-page.yml` publishes it to WordPress (needs the `WP_GMP_PAGE_ID` secret)
- `smartmoney/investors/*.json` + `scripts/investor_profiles.py` + `scripts/publish_investor_pages.py` — the Big-Investor profile pages (/smart-money/ and 15 child pages such as /smart-money/vijay-kedia-portfolio/). Every weekday, right after the Smart Money Tracker run, new NSE bulk/block deals by these investors are added (matched on whole names listed under `aliases`), the prices behind "on paper" gains are refreshed, and the pages are published to WordPress. New pages are created as drafts. Holdings are edited by hand once a quarter in each investor's JSON file.
