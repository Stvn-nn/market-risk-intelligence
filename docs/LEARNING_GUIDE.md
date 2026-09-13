# Understand the project, one layer at a time

## The flow

1. `app.py` collects a ticker and benchmark from a form.
2. `providers.py` validates the symbol and checks the SQLite cache.
3. `worker.py` requests daily market history in a separate process with a deadline.
4. `analytics.py` validates observations and calculates metrics.
5. `charts.py` turns those observations into interactive Plotly figures.
6. Streamlit displays figures and explanations; `report.py` builds a portable HTML snapshot with script-free chart images.

The API in `market_risk/api.py` reuses the same calculations. It does not duplicate the finance formulas. This is useful backend design: multiple interfaces can call one tested analysis layer.

## A learning sequence

**Session 1 — Python and Pandas:** open `analytics.py`. Trace `price_metrics`. For closing prices 100, 120, 90, 110, calculate the period return and drawdown by hand. Expected: +10% return and −25% maximum drawdown. Run the corresponding test.

**Session 2 — Data validation:** read `validate_prices`. Explain why duplicate dates, negative volume, or a high below the closing price would cause misleading results. Add one malformed row to a copy of a sample CSV and observe the error.

**Session 3 — Statistics:** read `anomaly_signals`. Explain why `.shift(1)` comes before `.rolling(30)`. Without the shift, the current observation would influence its own comparison distribution. Future observations must never alter past flags.

**Session 4 — Backend reliability:** trace `live_prices` and `cache.py`. Explain the difference between a cached response and fresh data, why the retrieval timestamp matters, and why a process deadline is stronger than an unbounded fetch.

**Session 5 — Explainability:** trace `risk_index`. Identify the weights and thresholds. Explain how missing SEC data reduces coverage but does not imply low risk. Change one weight only after deciding what hypothesis the change expresses.

**Session 6 — Own a change:** choose a small extension, describe the goal, implement it, test the result, and commit it. For example: add a 100-day moving average toggle, add a sector benchmark preset, or improve a chart's text explanation. Keep the baseline tests passing.

## Interview discussion points

- Problem: price charts show what happened, but do not explain risk drivers or data gaps.
- Design: separate fetching, validation, calculations, and presentation so each can be understood and checked independently.
- Reliability: requests have time limits; missing data is visible; the demo is reproducible and explicitly synthetic.
- Tradeoff: a transparent z-score is easier to audit than a more complex model, but it assumes a useful recent reference distribution and may flag regime changes imperfectly.
- Limitation: the risk index is a heuristic. Demonstrating polished software does not establish investment predictive power.
- Next research step: evaluate anomaly detection against held-out labeled or carefully constructed cases, and compare false-positive rates across market regimes.

## Honest project presentation

This version was implemented with AI assistance. Before presenting it as your work, run it yourself, learn the calculations, make and document changes, and be ready to explain what you personally contributed. Do not describe this as Deloitte employment or a commissioned Deloitte product.

After you have done those steps, you can adapt this factual project description:

> Developed and extended a Python market-risk dashboard with interactive price charts, benchmark analysis, anomaly flags, and explainable risk metrics; integrated public-data adapters and automated checks for calculation accuracy and invalid-input handling.

Only retain claims that match your actual contributions. Do not add user counts, prediction accuracy, business savings, or professional deployment claims without evidence.
