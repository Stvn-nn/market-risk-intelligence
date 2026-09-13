# Market Risk Intelligence Dashboard

A Python research dashboard that connects price behavior, company financials, and economic conditions through transparent risk calculations.

**Type any Yahoo Finance-supported ticker** into the sidebar: the app is not limited to the five synthetic examples. Examples include `TSLA`, `VTI`, `BRK-B`, and `7203.T`. Availability depends on the provider and the instrument's history. The app never presents invented observations as fetched market data.

Open `docs/DEMO_REPORT.html` in a browser for a synthetic research snapshot with embedded charts without installing Python. This report is a snapshot, not the live ticker-lookup app.

An independent student portfolio project, created with AI assistance to support learning in computer science, data analytics, and finance. No investment recommendations or order execution.

## Start here

Use **Python 3.12**. Download and extract the project, then open a terminal in the folder containing `app.py`.

Windows PowerShell (no activation-script policy changes needed):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the local address printed by Streamlit. The dashboard starts on a clearly labeled synthetic example. To see actual provider history, enter a ticker under **Market lookup** and press **Load market data**. `SPY` is the default S&P 500 ETF benchmark proxy; replace it with a suitable market or sector benchmark.

After the first installation, Windows users can double-click `START_WINDOWS.bat` to launch the app. See [START_HERE.md](START_HERE.md) for a slower walkthrough and troubleshooting.

## What it includes

| Area | Implemented behavior |
| --- | --- |
| Ticker lookup | Free-text provider symbols, custom benchmark, invalid-symbol errors, explicit active dataset label |
| Charts | Candlestick/line, volume, moving averages, benchmark rebasing, selectable analysis windows |
| Risk metrics | Returns, annualized volatility, beta, maximum drawdown |
| Anomaly detection | Trailing 30-return z-score with no future observations in the detector |
| Risk index | Visible component scores, formulas, weights, and missing-data coverage |
| Company financials | SEC annual US-GAAP liabilities/assets, current ratio, net margin; period and filing matching |
| Economic context | FRED 10-year Treasury yield, unemployment, CPI inflation; monthly yield association |
| Scenarios | Linear benchmark/yield sensitivity with explicit assumptions |
| Exports | Selected prices CSV and self-contained HTML research report with embedded chart images |
| Reliability | 25-second hard deadline per price worker, HTTP timeouts, no network retries, SQLite TTL cache |
| Interface | Dark theme, green increases, red decreases, numeric signs and text labels |
| Engineering | Separate providers/analytics/UI, automated tests, optional FastAPI endpoints, GitHub Actions |

## Data and credentials

**Market prices:** fetched via yfinance. OHLC is split/dividend adjusted. It is daily research history, not a guaranteed real-time quote feed. Price cache TTL is one hour. Respect provider data-use terms; yfinance describes its research/personal-use context in its [documentation](https://ranaroussi.github.io/yfinance/).

**SEC financials:** enter your contact email/User-Agent in the Company financials tab, then select **Load annual SEC financials**. For symbols beyond the starter companies, the adapter resolves the company through SEC's ticker mapping. ETFs and unsupported/non-US-GAAP filers may not have compatible ratios. The SEC publishes [companyfacts API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

**FRED:** enter your own API key in the Economic context tab, then select **Load economic indicators**. FRED requires a registered key for these [API requests](https://fred.stlouisfed.org/docs/api/api_key.html). The adapter uses the [series observations endpoint](https://fred.stlouisfed.org/docs/api/fred/series_observations.html).

You can instead set `SEC_USER_AGENT` and `FRED_API_KEY` as environment variables before launching. `.env.example` documents their names; the app does **not** automatically load `.env`. Keys are not committed, included in reports, or used as cache keys. External requests transmit the necessary identifier to the relevant provider.

**CSV:** upload daily OHLCV with `Date, Open, High, Low, Close, Volume`, at least 31 rows. Optionally upload a benchmark. Use consistently adjusted OHLC if corporate actions matter; a checkbox records your declaration, but does not adjust the file. Sample CSVs in `data/` are synthetic fixtures, not historical prices.

## Data quality and limitations

- An unavailable market request leaves the prior dataset visible under its original ticker and source, with an error notice. It never silently replaces a requested symbol with synthetic data.
- SEC/FRED are loaded explicitly, not automatically every time a tab or slider changes. They cache for 24 hours.
- Short/illiquid histories, provider outages, unsupported symbols, and rate limits can prevent lookup. Beta requires 30 matched return intervals; macro fitting needs 12 complete monthly changes.
- A 252-observation annualization convention is designed around trading-day equity history. Other instrument calendars may require different assumptions.
- Cross-currency comparisons use local-currency returns; no FX conversion is performed.
- The risk index is an illustrative heuristic, not a validated probability or prediction. Scores with different available components are not directly comparable.
- SEC data is the latest annual filing. FRED values may be revised. Neither is a point-in-time backtest dataset.
- Synthetic data is deterministic and intentionally contains unusual moves. Those demonstration flags do not establish detector accuracy on real markets.

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the formulas and [docs/VALIDATION.md](docs/VALIDATION.md) for verified results and integration limits.

## Tests and optional API

Install the development requirements using your virtual environment's Python, then run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn market_risk.api:app --host 127.0.0.1 --port 8000
```

The `python` commands above assume your virtual environment is activated; otherwise use the same full virtual-environment Python path as in setup.

API routes: `/health`, `/analysis/AAPL` (synthetic), and `/analysis/TSLA?live=true&benchmark=SPY` (provider-backed). `/docs` documents the API locally. Bind to localhost for development. Authentication, multi-user quotas, and production hosting are not included.

Possible future work: point-in-time economic vintages, sector-specific financial scoring, out-of-sample anomaly evaluation, exchange-calendar-aware annualization, and a PostgreSQL adapter. These are future extensions, not implemented claims.
