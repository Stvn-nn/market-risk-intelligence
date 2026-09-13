"""Portable HTML report with embedded chart images; no scripts or network required."""
from datetime import datetime, timezone
from html import escape
import pandas as pd
from .report_charts import price_volume_png, comparison_png, embedded_png


def export_report(ticker, benchmark_name, prices, benchmark, metrics, signals, risk, meta, financials=None, macro=None):
    e = lambda v: escape(str(v))
    mode = 'SYNTHETIC DEMONSTRATION — NOT REAL MARKET DATA' if meta.get('synthetic') else e(meta['source'])
    chart_label = f'{ticker} · SYNTHETIC DEMO' if meta.get('synthetic') else f'{ticker} · closing prices & volume'
    chart = embedded_png(price_volume_png(prices,signals,chart_label), f'{ticker}: closing prices, moving averages, unusual moves, and daily volume')
    compare = embedded_png(comparison_png(prices,benchmark,ticker,benchmark_name), f'{ticker} and {benchmark_name}, rebased to 100') if benchmark is not None else '<p>Benchmark unavailable.</p>'
    component_table = pd.DataFrame(risk['components']).to_html(index=False,escape=True,float_format=lambda v:f'{v:.2f}')
    flagged = signals[signals.flag][['return','z_score']].copy()
    flagged['return'] = flagged['return'].map(lambda x:f'{x:+.2%}')
    flags = flagged.to_html(escape=True)
    financial_html = pd.DataFrame([financials]).to_html(index=False,escape=True) if financials else '<p>Company financials unavailable; omitted from score.</p>'
    macro_text = e(macro) if macro else 'Yield sensitivity unavailable; omitted from score.'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(ticker)} | Market Risk Intelligence</title>
<style>body{{background:#0a1019;color:#e5eaf2;font:16px/1.6 system-ui,sans-serif;margin:0;padding:36px}}main{{max-width:1160px;margin:auto}}h1{{font-size:42px;line-height:1.15}}h2{{margin-top:36px}}.muted{{color:#a4afc0}}.badge{{color:#fbbf24;border:1px solid #655027;padding:10px 16px;border-radius:10px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}.card{{background:#101722;border:1px solid #263346;padding:22px;border-radius:12px}}.value{{font-size:26px;font-weight:650}}table{{border-collapse:collapse;font-size:14px;max-width:100%}}td,th{{padding:10px;border:1px solid #263346;text-align:left}}.table{{overflow:auto}}a{{color:#83b5ff}}@media(max-width:700px){{body{{padding:18px}}.grid{{grid-template-columns:1fr 1fr}}h1{{font-size:30px}}}}</style></head><body><main>
<p class="muted">MARKET / INTELLIGENCE · RESEARCH SNAPSHOT</p><h1>{e(ticker)} <span class="muted">Risk Intelligence</span></h1>
<p class="badge">{mode}</p><p>{metrics['start']} → {metrics['end']} · {metrics['observations']} observations · Currency: {e(meta.get('currency','Not supplied'))}</p>
<div class="grid"><div class="card">Period return<div class="value" style="color:{'#4ade80' if metrics['period_return']>=0 else '#fb7185'}">{metrics['period_return']:+.2%}</div></div><div class="card">Annualized volatility<div class="value">{metrics['annualized_volatility']:.2%}</div></div><div class="card">Maximum drawdown<div class="value" style="color:#fb7185">{metrics['max_drawdown']:.2%}</div></div><div class="card">Heuristic risk index<div class="value">{risk['score']:.1f} / 100</div></div></div>
<h2>Price & volume</h2>{chart}<p class="muted">Embedded chart snapshot. The Python dashboard provides interactive charts. Price segments: green increases, red decreases; volume bars follow close versus open.</p><h2>Benchmark comparison</h2>{compare}<h2>Explainable risk index</h2><p>{risk['label']} · Available component weight: {risk['coverage']}%. Available weights are renormalized. This is a descriptive heuristic, not a probability or a forecast.</p><div class="table">{component_table}</div>
<h2>Unusual price movements</h2><p>Daily return versus the previous 30 returns; threshold |z| ≥ 3. No future observations enter a day's detector.</p><div class="table">{flags}</div>
<h2>Company financials</h2><div class="table">{financial_html}</div><h2>Yield sensitivity</h2><p>{macro_text}</p>
<h2>Provenance & limitations</h2><p>Retrieved: {e(meta.get('retrieved_utc','Synthetic fixture'))}. Adjustment: {e(meta.get('adjustment','Synthetic prices'))}. Generated: {datetime.now(timezone.utc).isoformat()}.</p>
<p>252 observations per year are assumed. Beta uses matched asset/benchmark dates. Foreign-market comparisons use local currencies without FX adjustment. Economic associations are historical and do not establish causation. SEC data uses the latest annual US-GAAP filing, not point-in-time backtesting data. The risk index uses illustrative thresholds and is not calibrated or independently validated.</p><p>Educational analytics project. No trading or order execution. Independent portfolio project; not affiliated with Deloitte.</p>
<p>Sources: <a href="https://ranaroussi.github.io/yfinance/">yfinance</a> · <a href="https://www.sec.gov/search-filings/edgar-application-programming-interfaces">SEC EDGAR</a> · <a href="https://fred.stlouisfed.org/docs/api/fred/">FRED</a></p></main></body></html>'''
