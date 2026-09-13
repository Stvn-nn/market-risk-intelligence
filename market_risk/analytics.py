"""Pure calculations. Returns are decimals; rates are percentage points."""
from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def validate_prices(raw: pd.DataFrame, minimum: int = 31) -> pd.DataFrame:
    """Reject bad inputs rather than silently changing financial observations."""
    frame = raw.copy()
    frame.columns = [str(c).strip().lower().replace(' ', '_') for c in frame.columns]
    if 'date' not in frame.columns:
        raise ValueError('CSV needs a Date column.')
    needed = ['open', 'high', 'low', 'close', 'volume']
    missing = set(needed) - set(frame.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    frame['date'] = pd.to_datetime(frame['date'], errors='coerce', utc=True).dt.tz_convert(None).dt.normalize()
    if frame['date'].isna().any():
        raise ValueError('Every row needs a valid date.')
    if frame['date'].duplicated().any():
        raise ValueError('Duplicate dates found. Provide one row per trading date.')
    for col in needed:
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    if not np.isfinite(frame[needed].to_numpy(dtype=float)).all():
        raise ValueError('Prices and volume must be finite numbers with no blanks.')
    if (frame[['open', 'high', 'low', 'close']] <= 0).any().any() or (frame['volume'] < 0).any():
        raise ValueError('Prices must be positive and volume cannot be negative.')
    if ((frame['high'] < frame[['open', 'close', 'low']].max(axis=1)) |
        (frame['low'] > frame[['open', 'close', 'high']].min(axis=1))).any():
        raise ValueError('OHLC inconsistent: High must be highest and Low must be lowest.')
    if len(frame) < minimum:
        raise ValueError(f'At least {minimum} daily observations are required.')
    return frame[['date', *needed]].sort_values('date').set_index('date')


def price_metrics(prices: pd.DataFrame, benchmark: pd.DataFrame | None = None) -> dict:
    close = prices['close']
    returns = close.pct_change(fill_method=None).dropna()
    beta = correlation = None
    overlap = 0
    if benchmark is not None:
        # Align prices FIRST so the return intervals match, even with missing dates.
        paired = pd.concat([close.rename('asset'), benchmark['close'].rename('benchmark')], axis=1).dropna()
        pair_returns = paired.pct_change(fill_method=None).dropna()
        overlap = len(pair_returns)
        if overlap >= 30 and pair_returns['benchmark'].var(ddof=1) > 1e-15:
            beta = float(pair_returns.cov().loc['asset', 'benchmark'] / pair_returns['benchmark'].var(ddof=1))
            value = float(pair_returns.corr().loc['asset', 'benchmark'])
            correlation = value if np.isfinite(value) else None
    return {
        'price': float(close.iloc[-1]),
        'daily_return': float(returns.iloc[-1]),
        'period_return': float(close.iloc[-1] / close.iloc[0] - 1),
        'annualized_volatility': float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        'max_drawdown': float((close / close.cummax() - 1).min()),
        'beta': beta, 'correlation': correlation, 'benchmark_return_intervals': overlap,
        'observations': len(prices), 'start': str(close.index[0].date()), 'end': str(close.index[-1].date()),
    }


def anomaly_signals(prices: pd.DataFrame, window: int = 30, threshold: float = 3.0) -> pd.DataFrame:
    """Today's move is compared ONLY with prior returns, never future observations."""
    ret = prices['close'].pct_change(fill_method=None)
    history = ret.shift(1).rolling(window, min_periods=window)
    mean, sd = history.mean(), history.std(ddof=1)
    score = (ret - mean) / sd.where(sd > 1e-12)
    # A nonzero deviation after a truly constant window is an unbounded z-score.
    constant = sd.le(1e-12) & sd.notna()
    score = score.mask(constant & (ret - mean).abs().le(1e-12), 0.0)
    score = score.mask(constant & (ret - mean).gt(1e-12), np.inf)
    score = score.mask(constant & (ret - mean).lt(-1e-12), -np.inf)
    return pd.DataFrame({'return': ret, 'z_score': score, 'flag': score.abs().ge(threshold), 'eligible': sd.notna()})


def macro_sensitivity(prices: pd.DataFrame, yields: pd.Series | None) -> dict | None:
    """Monthly return vs monthly 10Y yield change; descriptive OLS, not causation."""
    if yields is None or yields.empty:
        return None
    close = prices['close'].resample('ME').last()
    yield_month = yields.resample('ME').last()
    paired = pd.concat([close.rename('close'), yield_month.rename('yield')], axis=1).dropna()
    # Exclude the incomplete final calendar month.
    end = min(prices.index.max(), yields.index.max())
    paired = paired[paired.index <= end]
    # Changes must be between consecutive calendar months, not across missing months.
    paired = paired.asfreq('ME')
    data = pd.concat([paired['close'].pct_change(fill_method=None).rename('return'), paired['yield'].diff().rename('yield_change')], axis=1).dropna()
    if len(data) < 12 or data['yield_change'].var(ddof=1) < 1e-12:
        return None
    slope = data.cov().loc['return', 'yield_change'] / data['yield_change'].var(ddof=1)
    corr = data.corr().loc['return', 'yield_change']
    return {'slope': float(slope), 'r_squared': float(corr**2) if np.isfinite(corr) else 0.0, 'months': len(data)}


def risk_index(metrics: dict, signals: pd.DataFrame, financials: dict | None = None, macro: dict | None = None) -> dict:
    """Documented heuristic; missing components reduce coverage, not measured risk."""
    components = []
    def add(name, value, weight, explanation):
        components.append({'component': name, 'score': round(float(np.clip(value, 0, 100)), 1), 'weight': weight, 'explanation': explanation})
    market = 0.5 * metrics['annualized_volatility'] / .60 + 0.5 * abs(metrics['max_drawdown']) / .50
    add('Market variability', market * 100, .40, 'Equal mix: annualized volatility / 60% and drawdown magnitude / 50%; capped at 100.')
    if metrics['beta'] is not None:
        add('Benchmark sensitivity', abs(metrics['beta']) / 2 * 100, .15, 'Absolute beta / 2, capped at 100.')
    eligible = signals['eligible']
    if eligible.any():
        add('Unusual moves', signals.loc[eligible, 'flag'].mean() / .10 * 100, .15, 'Flagged share of eligible days / 10%; capped at 100.')
    if financials and financials.get('liabilities_assets') is not None:
        add('Balance-sheet leverage', financials['liabilities_assets'] * 100, .15, 'Total liabilities / assets, capped at 100; sector context matters.')
    if macro:
        add('Yield sensitivity', abs(macro['slope']) / .25 * 100, .15, 'Absolute fitted monthly return per +1 percentage point yield change / 25%; capped at 100.')
    coverage = sum(c['weight'] for c in components)
    score = sum(c['score'] * c['weight'] for c in components) / coverage
    return {'score': round(score, 1), 'coverage': round(coverage * 100), 'components': components,
            'label': 'Lower' if score < 33 else 'Moderate' if score < 66 else 'Elevated'}


def scenario_effect(beta: float | None, market_percent: float, macro: dict | None, yield_bps: float) -> dict:
    if beta is None:
        raise ValueError('Scenario requires a benchmark beta from at least 30 matched return intervals.')
    if yield_bps != 0 and macro is None:
        raise ValueError('Yield scenario requires at least 12 matched monthly changes.')
    market = beta * market_percent / 100
    rates = macro['slope'] * yield_bps / 100 if macro else 0.0
    return {'market_effect': market, 'yield_effect': rates, 'combined': market + rates}
