import subprocess
import pytest
from market_risk import cache
from market_risk.providers import normalize_ticker,parse_companyfacts,live_prices,DataUnavailable


@pytest.mark.parametrize('symbol',['tsla','VTI','BRK-B','7203.T','^GSPC','BTC-USD','EURUSD=X'])
def test_arbitrary_provider_symbols(symbol):
    assert normalize_ticker(' '+symbol+' ')==symbol.upper()


@pytest.mark.parametrize('symbol',['','../../etc/passwd','AAPL;ls','$(whoami)','A'*21])
def test_invalid_symbol_syntax(symbol):
    with pytest.raises(DataUnavailable): normalize_ticker(symbol)


def test_sec_ratios_match_filing_and_annual_duration():
    def obs(value,start=None,filed='2025-02-01'):
        r={'val':value,'end':'2024-12-31','filed':filed,'form':'10-K'}
        if start:r['start']=start
        return r
    facts={}
    for tag,rows in {'Assets':[obs(100)],'Liabilities':[obs(60)],'AssetsCurrent':[obs(40)],
        'LiabilitiesCurrent':[obs(20)],'NetIncomeLoss':[obs(12,'2024-01-01'),obs(999,'2024-10-01')],
        'Revenues':[obs(120,'2024-01-01'),obs(9999,'2024-01-01',filed='2025-03-01')]}.items():
        facts[tag]={'units':{'USD':rows}}
    result=parse_companyfacts({'facts':{'us-gaap':facts}})
    assert result['net_margin']==pytest.approx(.1)
    assert result['current_ratio']==2
    assert result['liabilities_assets']==.6


def test_no_supported_sec_fields():
    with pytest.raises(DataUnavailable): parse_companyfacts({'facts':{}})


def test_cache_expires(tmp_path,monkeypatch):
    monkeypatch.setenv('MARKET_RISK_CACHE',str(tmp_path/'cache.db'))
    cache.put('key',{'value':42})
    assert cache.get('key')[0]['value']==42
    assert cache.get('key',ttl=-1) is None


def test_market_timeout_is_bounded(monkeypatch):
    monkeypatch.setattr(cache,'get',lambda *a,**k:None)
    def timeout(*a,**kw):
        assert kw['timeout']==25
        raise subprocess.TimeoutExpired(a[0],25)
    monkeypatch.setattr(subprocess,'run',timeout)
    with pytest.raises(DataUnavailable,match='25 seconds'):live_prices('TSLA')


def test_market_empty_response_does_not_become_demo(monkeypatch):
    monkeypatch.setattr(cache,'get',lambda *a,**kw:None)
    monkeypatch.setattr(subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],1,stdout='{"error":"empty"}'))
    with pytest.raises(DataUnavailable):live_prices('NOTAREALTICKER')
