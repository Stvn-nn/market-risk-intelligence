from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'


def test_app_demo_controls_and_report():
    app=AppTest.from_file(str(APP),default_timeout=15).run()
    assert not app.exception
    assert len(app.tabs)==5
    app.sidebar.select_slider[0].set_value('3M').run()
    assert not app.exception
    next(r for r in app.radio if r.label=='Chart style').set_value('Line').run()
    assert not app.exception
    app.sidebar.radio[0].set_value('Sample data').run()
    app.sidebar.selectbox[0].select('NVDA').run()
    next(b for b in app.button if b.label=='Load synthetic sample').click().run()
    assert app.session_state.dataset['ticker']=='NVDA'
    next(b for b in app.button if b.label=='Prepare HTML report').click().run()
    assert 'SYNTHETIC DEMONSTRATION' in app.session_state.report
    assert not app.exception


def test_custom_symbol_success_and_failure_keeps_label(monkeypatch):
    from market_risk.demo import demo_prices
    def fake_live(ticker,benchmark,refresh):
        assert ticker=='TSLA'
        return demo_prices('AAPL'),demo_prices('SPY'),{'source':'Mock provider','synthetic':False,'currency':'USD','retrieved_utc':'test','adjustment':'Test fixture'},None
    monkeypatch.setattr('market_risk.providers.load_market_pair',fake_live)
    app=AppTest.from_file(str(APP),default_timeout=15).run()
    app.sidebar.text_input[0].set_value('TSLA')
    next(b for b in app.button if b.label=='Load market data').click().run()
    assert app.session_state.dataset['ticker']=='TSLA'
    assert not app.exception
    app.sidebar.text_input[0].set_value('../../oops')
    next(b for b in app.button if b.label=='Load market data').click().run()
    assert app.error
    assert app.session_state.dataset['ticker']=='TSLA'
    assert not app.exception
