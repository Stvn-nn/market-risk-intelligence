import numpy as np
import pandas as pd
import pytest
from market_risk.analytics import validate_prices,price_metrics,anomaly_signals,risk_index,scenario_effect,macro_sensitivity
from market_risk.demo import demo_prices


def frame(values,index=None):
    values=np.array(values,dtype=float)
    return pd.DataFrame({'open':values,'high':values,'low':values,'close':values,'volume':100},index=index if index is not None else pd.bdate_range('2024-01-01',periods=len(values),name='date'))


def test_return_drawdown_known_path():
    m=price_metrics(frame([100,120,90,110]))
    assert m['period_return']==pytest.approx(.10)
    assert m['max_drawdown']==pytest.approx(-.25)
    assert m['daily_return']==pytest.approx(110/90-1)


def test_beta_recovers_known_exposure():
    rng=np.random.default_rng(8)
    r=rng.normal(0,.01,80)
    asset=frame(100*np.cumprod(1+2*r))
    bench=frame(100*np.cumprod(1+r))
    assert price_metrics(asset,bench)['beta']==pytest.approx(2)


def test_beta_missing_dates_aligns_intervals():
    p=demo_prices('AAPL')
    b=demo_prices('SPY').drop(p.index[::7])
    aligned=pd.concat([p.close,b.close],axis=1).dropna().pct_change(fill_method=None).dropna()
    expected=aligned.iloc[:,0].cov(aligned.iloc[:,1])/aligned.iloc[:,1].var()
    assert price_metrics(p,b)['beta']==pytest.approx(expected)


def test_constant_benchmark_unavailable():
    p=demo_prices('AAPL').iloc[:100]
    b=frame(np.ones(100)*100,index=p.index)
    assert price_metrics(p,b)['beta'] is None


def test_no_lookahead_in_detector():
    p=demo_prices('AAPL')
    before=anomaly_signals(p.iloc[:400])
    after=anomaly_signals(p)
    pd.testing.assert_frame_equal(before,after.iloc[:400])


def test_constant_window_detects_new_jump():
    signal=anomaly_signals(frame([100]*40+[150]))
    assert bool(signal.iloc[-1]['flag'])
    assert np.isposinf(signal.iloc[-1]['z_score'])
    assert not signal.iloc[:31].eligible.any()


def test_missing_score_components_reduce_coverage():
    p=demo_prices('AAPL')
    score=risk_index(price_metrics(p),anomaly_signals(p))
    assert score['coverage']==55
    expected=sum(c['score']*c['weight'] for c in score['components'])/.55
    assert score['score']==pytest.approx(expected,abs=.051)
    assert 0<=score['score']<=100


def test_scenario_basis_point_conversion():
    effect=scenario_effect(1.2,-5,{'slope':-.03},100)
    assert effect['combined']==pytest.approx(-.09)
    with pytest.raises(ValueError):
        scenario_effect(None,-5,None,0)
    with pytest.raises(ValueError):
        scenario_effect(1,-5,None,100)


@pytest.mark.parametrize('bad',['duplicate','nan','negative','ohlc','infinity','short'])
def test_invalid_csv_is_rejected(bad):
    raw=demo_prices('AAPL').iloc[:40].reset_index()
    if bad=='duplicate': raw.loc[1,'date']=raw.loc[0,'date']
    if bad=='nan': raw.loc[0,'close']=np.nan
    if bad=='negative': raw.loc[0,'volume']=-1
    if bad=='ohlc': raw.loc[0,'high']=1
    if bad=='infinity': raw.loc[0,'open']=np.inf
    if bad=='short': raw=raw.iloc[:10]
    with pytest.raises(ValueError): validate_prices(raw)


def test_valid_csv_sorts_and_normalizes():
    raw=demo_prices('MSFT').iloc[:40].reset_index().iloc[::-1]
    raw.columns=[x.title() for x in raw.columns]
    p=validate_prices(raw)
    assert p.index.is_monotonic_increasing
    assert len(p)==40


def test_macro_fit_recovers_monthly_association():
    dates=pd.date_range('2022-01-31',periods=36,freq='ME')
    dy=np.random.default_rng(6).normal(0,.1,36)
    yields=pd.Series(3+dy.cumsum(),index=dates)
    p=frame(100*np.cumprod(1+dy*.20),index=dates)
    fit=macro_sensitivity(p,yields)
    assert fit['slope']==pytest.approx(.20)
    assert fit['r_squared']==pytest.approx(1)


def test_constant_asset_has_no_correlation():
    b=demo_prices('SPY').iloc[:50]
    p=frame([100]*50,index=b.index)
    m=price_metrics(p,b)
    assert m['beta']==0
    assert m['correlation'] is None
