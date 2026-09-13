"""Bounded external reads, validated inputs, no silent substitution of demo data."""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests
from . import cache
from .analytics import validate_prices
from .demo import COMPANIES


class DataUnavailable(ValueError):
    pass


def normalize_ticker(value: str) -> str:
    symbol = value.strip().upper()
    if not re.fullmatch(r'[A-Z0-9^][A-Z0-9.\-^=]{0,19}', symbol):
        raise DataUnavailable('Enter a ticker such as AAPL, TSLA, BRK-B, ^GSPC, or 7203.T (up to 20 characters).')
    return symbol


def live_prices(ticker: str, refresh: bool = False):
    symbol = normalize_ticker(ticker)
    cached = None if refresh else cache.get('prices-v1:'+symbol, ttl=3600)
    if cached:
        payload, stamp = cached
    else:
        try:
            result = subprocess.run([sys.executable,'-m','market_risk.worker',symbol], capture_output=True,
                                    text=True, timeout=25, cwd=Path(__file__).resolve().parents[1])
        except subprocess.TimeoutExpired as exc:
            raise DataUnavailable(f'{symbol}: price request timed out after 25 seconds. Try again later or upload a CSV.') from exc
        try:
            payload = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise DataUnavailable(f'{symbol}: market provider did not return usable data.') from exc
        if result.returncode or 'error' in payload:
            raise DataUnavailable(f'{symbol}: no usable history. Check the symbol or try again later.')
        # Validate before persisting a provider response.
        validate_prices(pd.DataFrame(payload['rows']))
        cache.put('prices-v1:'+symbol,payload)
        stamp = datetime.now(timezone.utc).timestamp()
    prices = validate_prices(pd.DataFrame(payload['rows']))
    return prices, {'source':'Yahoo Finance via yfinance', 'synthetic':False,
                    'retrieved_utc':datetime.fromtimestamp(stamp,timezone.utc).isoformat(),
                    'cached':cached is not None, 'currency':payload.get('currency','Unknown'),
                    'exchange':payload.get('exchange','Unknown'), 'adjustment':'Split/dividend-adjusted OHLC'}


def load_market_pair(ticker: str, benchmark: str, refresh: bool = False):
    ticker, benchmark = normalize_ticker(ticker), normalize_ticker(benchmark)
    with ThreadPoolExecutor(max_workers=2) as pool:
        asset_task = pool.submit(live_prices, ticker, refresh)
        bench_task = pool.submit(live_prices, benchmark, refresh) if benchmark != ticker else asset_task
        prices, meta = asset_task.result()
        try:
            bench, bench_meta = bench_task.result()
            warning = None
            meta['benchmark_currency'] = bench_meta['currency']
            if meta['currency'] != bench_meta['currency']:
                warning = 'Asset and benchmark currencies differ. Returns use local currencies; no FX adjustment is made.'
        except (DataUnavailable, ValueError, OSError):
            bench, warning = None, 'Benchmark unavailable. Stock charts still work; beta and benchmark scenarios are unavailable.'
    return prices, bench, meta, warning


def fetch_json(url: str, params=None, headers=None) -> dict:
    try:
        # No retries: slow/unavailable services fail promptly instead of hanging the app.
        response = requests.get(url, params=params, headers=headers, timeout=(4,10))
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise DataUnavailable('The data service is unavailable or rejected this request. Check your settings and try later.') from exc


def parse_companyfacts(payload: dict) -> dict:
    """Latest annual 10-K data, matched by period AND filing; no YTD/quarter mixing."""
    facts = payload.get('facts',{}).get('us-gaap',{})
    tags = {
        'assets':['Assets'], 'liabilities':['Liabilities'],
        'current_assets':['AssetsCurrent'], 'current_liabilities':['LiabilitiesCurrent'],
        'income':['NetIncomeLoss'],
        'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet'],
    }
    def candidates(tag_names, annual=False):
        rows = []
        for priority, tag in enumerate(tag_names):
            for record in facts.get(tag,{}).get('units',{}).get('USD',[]):
                if record.get('form') not in ['10-K','10-K/A'] or 'val' not in record or not record.get('filed') or not record.get('end'):
                    continue
                if annual:
                    if not record.get('start'):
                        continue
                    days = (pd.Timestamp(record['end'])-pd.Timestamp(record['start'])).days
                    if not 330 <= days <= 380:
                        continue
                rows.append({**record,'priority':priority})
        return rows
    assets = candidates(tags['assets'])
    if not assets:
        raise DataUnavailable('No supported US-GAAP annual 10-K assets found. Some funds and foreign issuers do not supply these fields.')
    base = max(assets, key=lambda r:(r['end'], r['filed']))
    def match(name, annual=False, start=None):
        rows = [r for r in candidates(tags[name],annual) if r['end']==base['end'] and r['filed']==base['filed']]
        if start is not None:
            rows = [r for r in rows if r.get('start')==start]
        return min(rows, key=lambda r:r['priority']) if rows else None
    def ratio(a,b):
        return float(a['val']/b['val']) if a is not None and b is not None and b['val']>0 else None
    income = match('income',True)
    revenue = match('revenue',True,start=income.get('start')) if income else None
    return {'liabilities_assets':ratio(match('liabilities'),base),
            'current_ratio':ratio(match('current_assets'),match('current_liabilities')),
            'net_margin':ratio(income,revenue), 'period_end':base['end'],'filed':base['filed'],
            'form':base['form'], 'source':'SEC EDGAR companyfacts, latest annual filing',
            'notes':['Unavailable ratios are omitted. Annual figures may lag recent quarterly results.']}


def sec_financials(ticker: str, contact: str) -> dict:
    symbol = normalize_ticker(ticker)
    if '@' not in contact or len(contact)>200 or '\n' in contact or '\r' in contact:
        raise DataUnavailable('Enter a contact email for the SEC User-Agent, or set SEC_USER_AGENT in your environment.')
    existing = cache.get('sec-v1:'+symbol,ttl=86400)
    if existing:
        return existing[0]
    headers = {'User-Agent':'MarketRiskIntelligence '+contact, 'Accept-Encoding':'gzip, deflate'}
    cik = COMPANIES.get(symbol,(None,None))[1]
    if cik is None:
        mapping_cache = cache.get('sec-tickers-v1',ttl=86400)
        mapping = mapping_cache[0] if mapping_cache else fetch_json('https://www.sec.gov/files/company_tickers.json',headers=headers)
        if not mapping_cache:
            cache.put('sec-tickers-v1',mapping)
        match = next((r for r in mapping.values() if r['ticker'].upper().replace('.','-')==symbol.replace('.','-')),None)
        if match is None:
            raise DataUnavailable('This ticker has no match in the SEC company ticker list. Financial ratios are unavailable for this symbol.')
        cik = str(match['cik_str']).zfill(10)
    payload = fetch_json(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',headers=headers)
    parsed = parse_companyfacts(payload)
    parsed['retrieved_utc'] = datetime.now(timezone.utc).isoformat()
    cache.put('sec-v1:'+symbol,parsed)
    return parsed


def fred_macro(api_key: str) -> pd.DataFrame:
    if not re.fullmatch(r'[a-zA-Z0-9]{32}',api_key):
        raise DataUnavailable('Enter your 32-character FRED API key or set FRED_API_KEY in your environment.')
    existing = cache.get('fred-v1',ttl=86400)
    if existing:
        raw = pd.DataFrame(existing[0]['rows'])
        raw['date'] = pd.to_datetime(raw['date'])
        return raw.set_index('date')
    def fetch(series):
        payload = fetch_json('https://api.stlouisfed.org/fred/series/observations',params={
            'series_id':series,'api_key':api_key,'file_type':'json','observation_start':'2019-01-01'})
        raw = pd.DataFrame(payload.get('observations',[]))
        if raw.empty:
            raise DataUnavailable('FRED returned no observations.')
        return pd.Series(pd.to_numeric(raw['value'],errors='coerce').to_numpy(),index=pd.to_datetime(raw['date']),name=series).dropna()
    with ThreadPoolExecutor(max_workers=3) as pool:
        series = list(pool.map(fetch,['DGS10','UNRATE','CPIAUCSL']))
    frame = pd.concat(series,axis=1).sort_index().rename_axis('date')
    records = json.loads(frame.reset_index().to_json(orient='records',date_format='iso'))
    cache.put('fred-v1',{'rows':records})
    return frame
