"""Optional read-only API: python -m uvicorn market_risk.api:app --host 127.0.0.1"""
from fastapi import FastAPI, HTTPException, Query
from .analytics import price_metrics, anomaly_signals, risk_index
from .demo import demo_prices
from .providers import normalize_ticker, load_market_pair, DataUnavailable

app=FastAPI(title='Market Risk Intelligence',version='1.0.0',description='Educational market analytics. Live prices are optional; demo responses are explicitly synthetic.')


@app.get('/health')
def health():
    return {'status':'ok'}


@app.get('/analysis/{ticker}')
def analysis(ticker: str, benchmark: str=Query('SPY',max_length=20), live: bool=False):
    try:
        ticker, benchmark=normalize_ticker(ticker),normalize_ticker(benchmark)
        if live:
            prices, bench, meta, warning=load_market_pair(ticker,benchmark)
        else:
            prices, bench=demo_prices(ticker),demo_prices(benchmark)
            meta,warning={'source':'Synthetic demo','synthetic':True},None
        metrics=price_metrics(prices,bench)
        signals=anomaly_signals(prices)
        return {'ticker':ticker,'benchmark':benchmark,'provenance':meta,'warning':warning,
                'metrics':metrics,'risk_index':risk_index(metrics,signals),
                'anomaly_dates':[str(x.date()) for x in signals.index[signals.flag]]}
    except (ValueError,DataUnavailable) as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
