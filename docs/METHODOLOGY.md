# Methodology and boundaries

## Prices and returns

The provider path calls `Ticker.history(period='5y', interval='1d', auto_adjust=True)`. Daily OHLC is adjusted by yfinance. Daily prices are not guaranteed real-time quotes. Volume is the provider's reported daily volume. CSVs are validated but not automatically adjusted.

For closing price C at observation t, daily return is `C[t] / C[t-1] - 1`. Period return is `last close / first close - 1`. The selected period is measured backward from the last available price date.

Annualized volatility is the sample standard deviation (`ddof=1`) of daily returns multiplied by `sqrt(252)`. It is historical dispersion, not a loss probability. Irregular/missing trading dates and non-equity calendars can weaken this convention.

Maximum drawdown is the minimum of `close / running maximum close - 1` within the selected window. A peak before that window is not included.

## Benchmark comparison

Asset and benchmark prices are inner-joined by date BEFORE computing returns. This makes each pair span matching intervals when observations are missing. Beta is `cov(asset return, benchmark return) / var(benchmark return)`, using sample covariance/variance. At least 30 matched return intervals and nonzero benchmark variance are required.

Benchmark curves both start at 100 on the first overlapping date. They use local currencies. A mixed-currency warning does not substitute for FX conversion.

## Unusual movements

Each return is compared with the mean and sample standard deviation of the **previous** 30 returns. `z = (current return - prior mean) / prior standard deviation`. A flag occurs when `abs(z) >= 3`.

The shift happens before rolling statistics. Adding later rows cannot change earlier detector results; a regression test enforces this. Warm-up is 31 price observations. A nonzero deviation after a zero-variance history produces an infinite z-score and a flag; identical subsequent returns do not.

Detection runs on the full loaded history, then the chosen window is displayed. Moving-average lines and volatility/drawdown charts use the selected window, so their initial warm-up can differ. Outlier flags are descriptive and do not identify fraud, causation, or future movement. This is a transparent statistical detector, not a trained machine-learning model.

## SEC ratios

Only USD units and annual US-GAAP 10-K/10-K/A records are used. The parser selects the latest asset period (then latest filing), and matches other facts to the same end date and filing date. Annual income/revenue durations must be 330–380 days and must have the same start date. This avoids mixing quarterly, year-to-date, annual, and mismatched restatement data.

- Liabilities/assets = total liabilities / total assets.
- Current ratio = current assets / current liabilities.
- Net margin = annual net income / annual revenue.

Missing/nonpositive denominators produce unavailable values. Tag coverage is deliberately limited; an omitted ratio is preferable to inventing one. Company extensions, foreign IFRS facts, and bank-specific ratios are not implemented. Current ratio is omitted in the bank demo. The latest filing is independent of the selected historical price window and is not valid for an as-of backtest.

## Economic context and monthly sensitivity

FRED series: `DGS10` (10-year Treasury yield, percent), `UNRATE` (unemployment, percent), `CPIAUCSL` (CPI index). CPI inflation is `100 * (index / index 12 months ago - 1)`. Changes in rates are percentage points, not percentage changes.

For yield sensitivity, prices and yields are sampled at month-end. The incomplete final month is excluded. Missing calendar months are not bridged. At least 12 paired monthly changes are required. With monthly stock return y and yield change x (in percentage points), the fitted slope is `cov(y,x)/var(x)`; R² is squared correlation. An intercept is implicit in the centered covariance estimator.

This fit uses the full loaded history, not only the selected chart window. Release dates and vintages are not modeled. Historical association does not show causal influence or forecast reliability.

## Explainable risk index

Component values are clipped to 0–100.

| Component | Base weight | Score before clipping |
| --- | --- | --- |
| Market variability | 40% | `100 * (0.5 * annualized volatility / 0.60 + 0.5 * abs(drawdown) / 0.50)` |
| Benchmark sensitivity | 15% | `100 * abs(beta) / 2` |
| Unusual moves | 15% | `100 * flagged eligible days / eligible days / 0.10` |
| Balance-sheet leverage | 15% | `100 * liabilities / assets` |
| Yield sensitivity | 15% | `100 * abs(monthly yield slope) / 0.25` |

The final index is `sum(available score * base weight) / sum(available base weights)`. Component scores are rounded to one decimal before aggregation; the final index is rounded to one decimal. Below 33 is labeled Lower, 33–below 66 Moderate, and 66+ Elevated.

Available component weight is shown separately as **coverage**. It measures completeness, not statistical confidence, accuracy, or data freshness. Missing inputs are not assigned a zero score. Scores with different coverage, horizons, or sectors should not be treated as apples-to-apples comparisons. Thresholds and weights are illustrative choices, not calibrated financial models.

## Scenarios

`market effect = beta * benchmark shock percent / 100`

`yield effect = monthly yield slope * yield shock basis points / 100`

The sum is a rough linear sensitivity illustration. Separately fitted market and yield relationships may overlap and double-count the same historical movements. The displayed beta uses the selected window while the yield slope uses full-history monthly data. No probability, confidence interval, trade, or profit projection is attached.

## Reliability and persistence

Each yfinance fetch runs in a subprocess that is killed after 25 seconds. Asset and benchmark requests run concurrently. Requests to SEC/FRED have a 4-second connect timeout and 10-second read timeout; these are socket timeouts rather than a whole-download deadline. There are no automatic request retries.

SQLite holds validated external price responses for one hour and SEC/FRED responses for 24 hours. It lives in the user's `.market-risk-intelligence` directory unless `MARKET_RISK_CACHE` is set. SQL keys are parameterized. Uploads stay in app session memory. The app does not create a remote database.

## References

- [yfinance history API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [FRED series observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
- [Streamlit Plotly charts](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
