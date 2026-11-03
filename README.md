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
