"""Deterministic synthetic fixtures. These are NOT real historical observations."""
import numpy as np
import pandas as pd

COMPANIES = {'AAPL': ('Apple', '0000320193'), 'MSFT': ('Microsoft', '0000789019'),
             'NVDA': ('NVIDIA', '0001045810'), 'AMZN': ('Amazon', '0001018724'),
             'JPM': ('JPMorgan Chase', '0000019617')}


def demo_prices(ticker: str) -> pd.DataFrame:
    tickers = [*COMPANIES, 'SPY']
    if ticker not in tickers:
        raise ValueError('Unknown demo ticker.')
    i = tickers.index(ticker)
    dates = pd.bdate_range('2023-01-03', '2025-12-31')
    market_rng = np.random.default_rng(2026)
    market = market_rng.normal(.00035, .009, len(dates))
    rng = np.random.default_rng(110 + i)
    beta = [1.1, .95, 1.65, 1.2, .85, 1][i]
    ret = market if ticker == 'SPY' else beta * market + rng.normal(.00012, [.008,.007,.016,.01,.009][i], len(dates))
    if ticker != 'SPY':
        ret[[220, 458, 697]] += [-.095, .09, -.07]
    close = [150, 250, 80, 110, 130, 380][i] * np.exp(np.cumsum(ret))
    op = np.r_[close[0], close[:-1]] * np.exp(rng.normal(0, .003, len(dates)))
    spread = rng.uniform(.001, .015, len(dates))
    return pd.DataFrame({'open': op, 'high': np.maximum(op,close)*(1+spread),
                         'low': np.minimum(op,close)*(1-spread), 'close': close,
                         'volume': rng.integers(8_000_000,70_000_000,len(dates))}, index=dates.rename('date'))


def demo_financials(ticker: str) -> dict:
    i = list(COMPANIES).index(ticker)
    return {'liabilities_assets': [.72,.46,.33,.61,.91][i],
            'current_ratio': [1.04,1.63,3.9,1.08,None][i],
            'net_margin': [.22,.31,.42,.09,.25][i],
            'period_end': '2025-12-31', 'filed': 'Synthetic fixture', 'form':'Demo',
            'source':'Synthetic illustrative ratios; not actual company financials',
            'notes':['Current ratio is omitted for JPM because bank balance sheets require different context.'] if ticker=='JPM' else []}


def demo_macro() -> pd.DataFrame:
    dates = pd.date_range('2022-01-31','2025-12-31',freq='ME')
    n = np.arange(len(dates))
    rng = np.random.default_rng(86)
    return pd.DataFrame({'DGS10':3.0+.026*n+.45*np.sin(n/3)+rng.normal(0,.12,len(n)),
                         'UNRATE':3.7+.008*n+.15*np.cos(n/4),
                         'CPIAUCSL':280*np.exp(.0025*n)}, index=dates.rename('date'))
