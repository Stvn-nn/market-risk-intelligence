# Validation record

Build date: September 12, 2026. Runtime: Linux, Python 3.12.

## Verified

`python -m pytest -q`: **37 passed** in the final run. Two upstream test-client deprecation warnings; no failing tests.

Checks cover known return/drawdown paths, recovery of known beta, matched benchmark intervals with missing dates, constant-series behavior, no look-ahead in the anomaly detector, risk-weight coverage, basis-point conversion, malformed CSV rejection, SEC annual-period/filing matching, cache expiry, arbitrary ticker syntax, bounded price-worker timeout handling, and unavailable-provider behavior.

Streamlit AppTest exercised the default demo, analysis-window changes, line/candlestick selection, switching sample tickers, report generation, a mocked successful custom `TSLA` fetch, and invalid-symbol handling that preserves the previously loaded ticker. The custom-symbol success test used a mocked provider response; it was not a live TSLA download.

The optional FastAPI test checked health, synthetic analysis, and a clear error for a symbol without a demo fixture. Streamlit was also started as a real local process: `/_stcore/health` returned **HTTP 200, ok**.

The self-contained demo HTML report and the two sample CSVs were generated from deterministic synthetic fixtures. These are not real company observations.

## Not verified end to end

- **Live market prices:** a TSLA request through the adapter returned no usable history; a direct Yahoo chart-endpoint diagnostic returned HTTP 429 (rate limited). No successful live market download is claimed.
- **Live SEC financials:** the network diagnostic timed out. The parser was verified against constructed filing data, not a fresh SEC response.
- **Live FRED observations:** no user FRED API key was supplied. The adapter is implemented but a credentialed integration request was not run.
- **Browser visual QA:** browser installation could not complete because its download timed out. Automated Streamlit interaction checks passed, but no browser-rendered screenshot or pixel-level visual verification is claimed.
- **Windows/macOS installation:** instructions are included; execution in these operating systems was not tested here.
- **GitHub publication/CI:** the source and workflow are prepared, but no user repository was created or pushed and no GitHub Actions result is claimed.

The app's input validation, explicit provenance, error messages, offline sample mode, and optional CSV import are designed to keep unavailable integrations from silently becoming false data.

## Report chart repair — September 13, 2026

The separately delivered HTML report was found to contain incomplete Plotly JavaScript; its archive copy retained the full script. Reports now embed PNG chart snapshots and contain no scripts, so rendering does not depend on JavaScript support or delivery of a large script bundle. The Python dashboard continues to use interactive Plotly charts.

Two report-specific regression checks passed with `python -m unittest discover -s tests -p test_report.py -v`: both embedded images decode correctly with substantive image content, and a missing benchmark still leaves a visible price/volume chart. The generated price/volume PNG was visually inspected. The prior 37-test result above describes the original build; the entire suite was not rerun for this focused report repair.
