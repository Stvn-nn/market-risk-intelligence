"""Run with: python -m streamlit run app.py"""
from datetime import datetime, timezone
from html import escape
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from market_risk.analytics import validate_prices, price_metrics, anomaly_signals, macro_sensitivity, risk_index, scenario_effect
from market_risk.charts import GREEN, RED, BLUE, style, price_chart, comparison_chart, risk_history
from market_risk.demo import COMPANIES, demo_prices, demo_financials, demo_macro
from market_risk.providers import DataUnavailable, normalize_ticker, load_market_pair, sec_financials, fred_macro
from market_risk.report import export_report

st.set_page_config(page_title='Market Risk Intelligence',page_icon='📈',layout='wide')
st.markdown('''<style>
.stApp {background:#0a1019;color:#e5eaf2}
[data-testid="stSidebar"] {background:#101722;border-right:1px solid #243043}
.block-container {padding-top:2rem;max-width:1550px}
h1 {letter-spacing:-.035em} h3 {letter-spacing:-.015em}
.eyebrow {font-size:11px;letter-spacing:.17em;color:#a4afc0;font-weight:700}
.hero {display:flex;align-items:center;gap:18px;margin:8px 0 6px}
.symbol {font-size:43px;font-weight:750;line-height:1.2}
.caption {color:#a4afc0;font-size:13px}
.kpi {padding:18px 20px;background:#101722;border:1px solid #263346;border-radius:12px;min-height:127px}
.kpi-label {font-size:12px;color:#a4afc0;margin-bottom:10px}
.kpi-value {font-size:29px;font-weight:650;line-height:1.2}
.kpi-note {font-size:12px;margin-top:9px;color:#a4afc0}
[data-testid="stTabs"] {margin-top:22px}
button:focus-visible,a:focus-visible,input:focus-visible {outline:2px solid #83b5ff!important;outline-offset:3px}
</style>''',unsafe_allow_html=True)


def demo_dataset(ticker='AAPL'):
    return {'ticker':ticker,'benchmark_name':'SPY','prices':demo_prices(ticker),'benchmark':demo_prices('SPY'),
            'financials':demo_financials(ticker),'macro':demo_macro(),
            'meta':{'source':'Synthetic sample','synthetic':True,'currency':'USD (illustrative)',
                    'retrieved_utc':'Fixed synthetic fixture','adjustment':'Synthetic OHLC'},'warning':None}


if 'dataset' not in st.session_state:
    st.session_state.dataset = demo_dataset()

with st.sidebar:
    st.markdown('<p class="eyebrow">MARKET / INTELLIGENCE</p>',unsafe_allow_html=True)
    st.markdown('### Research workspace')
    st.caption('Explore price behavior. Understand the risk behind the chart.')
    source = st.radio('Load data', ['Market lookup','Upload CSV','Sample data'])
    if source=='Market lookup':
        with st.form('market_lookup'):
            symbol = st.text_input('Ticker symbol','AAPL',help='Any symbol supported by Yahoo Finance. Examples: TSLA, VTI, BRK-B, 7203.T.')
            benchmark_symbol = st.text_input('Benchmark ticker','SPY',help='SPY is an S&P 500 ETF proxy. Choose a suitable benchmark for the asset.')
            refresh = st.checkbox('Refresh cached prices',False)
            submitted = st.form_submit_button('Load market data',type='primary',width='stretch')
        if submitted:
            try:
                active_symbol, active_bench = normalize_ticker(symbol), normalize_ticker(benchmark_symbol)
                with st.spinner('Loading daily history. Each price request has a 25-second limit…'):
                    prices, bench, meta, warning = load_market_pair(active_symbol,active_bench,refresh)
                st.session_state.dataset = {'ticker':active_symbol,'benchmark_name':active_bench,'prices':prices,
                    'benchmark':bench,'meta':meta,'financials':None,'macro':None,'warning':warning}
                st.success('Market history loaded.')
            except (DataUnavailable,ValueError,OSError) as exc:
                st.error(str(exc))
                st.warning('The previously loaded dataset remains displayed under its original label.')
    elif source=='Sample data':
        with st.form('demo_form'):
            sample_symbol = st.selectbox('Example company',list(COMPANIES),format_func=lambda x:f'{x} · {COMPANIES[x][0]}')
            if st.form_submit_button('Load synthetic sample',width='stretch'):
                st.session_state.dataset=demo_dataset(sample_symbol)
        st.caption('These five fixtures are invented examples. Market lookup accepts other tickers.')
    else:
        with st.form('csv_form'):
            csv_symbol=st.text_input('Dataset label','MYDATA',max_chars=20)
            asset_file=st.file_uploader('Asset prices CSV',type='csv')
            bench_file=st.file_uploader('Benchmark prices CSV (optional)',type='csv')
            currency=st.text_input('Quote currency','USD',max_chars=12)
            adjusted=st.checkbox('All OHLC columns are already split/dividend adjusted')
            csv_submit=st.form_submit_button('Analyze CSV',width='stretch')
        st.caption('Columns: Date, Open, High, Low, Close, Volume. At least 31 daily rows. Uploads stay in memory.')
        if csv_submit:
            try:
                if asset_file is None:
                    raise ValueError('Select an asset CSV first.')
                p=validate_prices(pd.read_csv(asset_file))
                b=validate_prices(pd.read_csv(bench_file)) if bench_file else None
                st.session_state.dataset={'ticker':normalize_ticker(csv_symbol),'benchmark_name':'CSV benchmark','prices':p,
                    'benchmark':b,'financials':None,'macro':None,'warning':None,
                    'meta':{'source':'User CSV','synthetic':False,'currency':currency,
                            'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                            'adjustment':'User-declared adjusted OHLC' if adjusted else 'Unadjusted or unspecified; splits/dividends may distort returns'}}
            except (ValueError,pd.errors.ParserError) as exc:
                st.error(str(exc))
                st.warning('The previously loaded dataset remains displayed.')
    st.divider()
    period=st.select_slider('Analysis window',options=['3M','6M','1Y','3Y','All'],value='1Y')
    st.caption('Windows end at the latest available observation, not necessarily today.')
    st.divider()
    st.caption('Educational research · No order execution\n\nIndependent portfolio project.')

D=st.session_state.dataset
ticker, benchmark_name, meta = D['ticker'],D['benchmark_name'],D['meta']
full=D['prices']
months={'3M':3,'6M':6,'1Y':12,'3Y':36}
cutoff=full.index.max()-pd.DateOffset(months=months[period]) if period!='All' else full.index.min()
prices=full.loc[full.index>=cutoff]
benchmark=D['benchmark']
if benchmark is not None:
    benchmark=benchmark.loc[(benchmark.index>=prices.index.min()) & (benchmark.index<=prices.index.max())]
    if len(benchmark)<2 or len(prices.index.intersection(benchmark.index))<2:
        benchmark=None
metrics=price_metrics(prices,benchmark)
# Compute detection on full available history before slicing, preserving the warm-up.
signals=anomaly_signals(full).reindex(prices.index)
macro_fit=macro_sensitivity(full,D['macro']['DGS10'].dropna() if D['macro'] is not None else None)
risk=risk_index(metrics,signals,D['financials'],macro_fit)

st.markdown('<p class="eyebrow">RESEARCH TERMINAL / MARKET RISK INTELLIGENCE</p>',unsafe_allow_html=True)
st.markdown(f'<div class="hero"><span class="symbol">{escape(ticker)}</span><span class="caption">Price behavior. Risk drivers. Clear evidence.</span></div>',unsafe_allow_html=True)
if meta['synthetic']:
    st.warning('SYNTHETIC DEMO — these are invented observations, not actual company prices or financials. Enter any supported ticker in the sidebar and choose Load market data.')
else:
    st.caption(f"{meta['source']} · {meta.get('currency','Unknown currency')} · Through {metrics['end']} · {meta['adjustment']}")
    age=(pd.Timestamp.now().normalize()-prices.index.max()).days
    if age>7:
        st.warning(f'Latest price is {age} calendar days old. This may be stale history or an inactive symbol.')
if D.get('warning'):
    st.warning(D['warning'])


def card(column,label,value,note,color=None):
    with column:
        st.markdown(f'<div class="kpi"><div class="kpi-label">{escape(label)}</div><div class="kpi-value" style="color:{color or "#e5eaf2"}">{escape(value)}</div><div class="kpi-note">{escape(note)}</div></div>',unsafe_allow_html=True)


cols=st.columns(4)
card(cols[0],'LATEST CLOSE',f'{metrics["price"]:,.2f}',f'{metrics["daily_return"]:+.2%} last observation · {meta.get("currency","Unknown")}',GREEN if metrics['daily_return']>=0 else RED)
card(cols[1],'PERIOD RETURN',f'{metrics["period_return"]:+.2%}',f'{metrics["start"]} → {metrics["end"]}',GREEN if metrics['period_return']>=0 else RED)
card(cols[2],'ANNUALIZED VOLATILITY',f'{metrics["annualized_volatility"]:.1%}','Daily variability × √252')
card(cols[3],'MAXIMUM DRAWDOWN',f'{metrics["max_drawdown"]:.1%}','Largest peak-to-trough decline',RED if metrics['max_drawdown']<0 else None)

tabs=st.tabs(['Overview','Risk & anomalies','Company financials','Economic context','Scenarios & report'])
with tabs[0]:
    left,right=st.columns([3,1])
    with left:
        st.subheader('Price & volume')
        controls=st.columns([2,2])
        kind=controls[0].radio('Chart style',['Candlestick','Line'],horizontal=True)
        averages=controls[1].checkbox('Moving averages',True)
        st.plotly_chart(price_chart(prices,signals,kind,averages),width='stretch',theme=None,config={'displaylogo':False})
        st.caption('Green candles: close ≥ open. Red candles: close < open. Diamonds mark unusual returns. Line segments use day-to-day direction.')
    with right:
        st.subheader('Risk overview')
        st.metric('Heuristic risk index',f'{risk["score"]:.1f} / 100')
        st.progress(risk['score']/100,text=f'{risk["label"]} · illustrative scale')
        st.caption(f'{risk["coverage"]}% of component weight available. Missing components are excluded and remaining weights renormalized.')
        st.metric('Benchmark beta','Unavailable' if metrics['beta'] is None else f'{metrics["beta"]:.2f}')
        st.caption('Historical sensitivity to the chosen benchmark. Beta 1.2 means an estimated 1.2% move per 1% benchmark move, before other factors.')
        st.metric('Unusual moves',int(signals.flag.sum()))
        st.caption(f'{metrics["observations"]} price observations in this window.')
    st.subheader(f'Performance vs {benchmark_name}')
    if benchmark is not None:
        st.plotly_chart(comparison_chart(prices,benchmark,ticker,benchmark_name),width='stretch',theme=None)
        st.caption('Series start at 100 on their first common date. Colors identify series; hover to inspect values.')
    else:
        st.info('Load a benchmark with overlapping dates to compare performance.')
    with st.expander('View and download chart data'):
        st.dataframe(prices.sort_index(ascending=False),width='stretch')
        st.download_button('Download selected prices CSV',prices.to_csv(),file_name=f'{ticker}_prices.csv',mime='text/csv')

with tabs[1]:
    st.subheader('Understand what drives the index')
    st.caption('Higher values mean more exposure under these illustrative thresholds. This score is not a probability of losing money.')
    st.dataframe(pd.DataFrame(risk['components']),hide_index=True,width='stretch',column_config={'weight':st.column_config.NumberColumn('Base weight',format='percent')})
    st.plotly_chart(risk_history(prices),width='stretch',theme=None)
    st.subheader('Unusual daily movements')
    flagged=signals.loc[signals.flag,['return','z_score']].copy()
    if flagged.empty:
        st.info('No returns exceeded the detector threshold in this window.')
    else:
        flagged.columns=['Daily return','Prior-window z-score']
        st.dataframe(flagged.sort_index(ascending=False).style.format({'Daily return':'{:+.2%}','Prior-window z-score':'{:+.2f}'}).map(lambda v:f'color: {GREEN if v>=0 else RED}',subset=['Daily return']),width='stretch')
    st.caption('Detector: each daily return versus the prior 30 returns, |z| ≥ 3. The first 31 price rows are warm-up. Flags identify statistical outliers, not their causes. No future data enters the rolling detector.')

with tabs[2]:
    st.subheader('Company financial health')
    if not meta['synthetic']:
        contact=st.text_input('SEC contact email / User-Agent',value=os.environ.get('SEC_USER_AGENT',''),type='password',help='Used only to identify SEC requests. Not saved in this project or included in reports.')
        if st.button('Load annual SEC financials'):
            try:
                with st.spinner('Reading the latest available annual SEC facts…'):
                    D['financials']=sec_financials(ticker,contact)
                st.rerun()
            except (DataUnavailable,ValueError,OSError) as exc:
                st.error(str(exc))
    financials=D['financials']
    if financials:
        c=st.columns(3)
        for col,key,label,fmt in [(c[0],'liabilities_assets','Liabilities / assets','.1%'),(c[1],'current_ratio','Current ratio','.2f'),(c[2],'net_margin','Annual net margin','.1%')]:
            value=financials.get(key)
            col.metric(label,format(value,fmt) if value is not None else 'Unavailable')
        st.caption(f"{financials['source']} · Period ended {financials['period_end']} · Filed {financials['filed']}")
        for note in financials.get('notes',[]):
            st.caption(note)
        st.info('Ratio interpretation depends on the industry. Banks in particular require different liquidity and leverage context. Financials use the latest annual filing, independently of the selected price window.')
    else:
        st.info('Load SEC data for a supported US reporting company. ETFs, some foreign issuers, and non-US-GAAP filers may not have these ratios; unavailable fields remain empty.')

with tabs[3]:
    st.subheader('The economic backdrop')
    if not meta['synthetic']:
        key=st.text_input('FRED API key',value=os.environ.get('FRED_API_KEY',''),type='password')
        if st.button('Load economic indicators'):
            try:
                with st.spinner('Loading Treasury yield, unemployment, and CPI…'):
                    D['macro']=fred_macro(key)
                st.rerun()
            except (DataUnavailable,ValueError,OSError) as exc:
                st.error(str(exc))
        st.caption('Use your own FRED key. It stays out of the source files, cache keys, and reports.')
    frame=D['macro']
    if frame is not None:
        cols=st.columns(3)
        for col,series,label in [(cols[0],'DGS10','10-year Treasury yield'),(cols[1],'UNRATE','Unemployment rate'),(cols[2],'CPIAUCSL','CPI inflation · year over year')]:
            values=frame[series].dropna()
            if series=='CPIAUCSL':
                values=values.resample('MS').first().pct_change(12,fill_method=None).dropna()*100
            change=float(values.iloc[-1]-values.iloc[-2])
            with col:
                st.metric(label,f'{values.iloc[-1]:.2f}%',f'{change:+.2f} pp',delta_color='normal')
                st.caption(f'Observation: {values.index[-1].date()} · Change vs prior observation')
        series_name=st.selectbox('Indicator chart',['DGS10','UNRATE','CPIAUCSL'],format_func=lambda x:{'DGS10':'10-year Treasury yield (%)','UNRATE':'Unemployment rate (%)','CPIAUCSL':'CPI price index (1982–84 = 100)'}[x])
        values=frame[series_name].dropna()
        fig=go.Figure(go.Scatter(x=values.index,y=values,mode='lines',line=dict(color=BLUE),name=series_name))
        st.plotly_chart(style(fig,300),width='stretch',theme=None)
        st.caption('Latest reported observations can have different dates and release lags. Historical FRED values can be revised. Green means an increase, not necessarily an improvement.')
        if macro_fit:
            st.write(f'Yield association: {macro_fit["slope"]:+.2%} monthly stock return per +1 percentage-point yield change; R² {macro_fit["r_squared"]:.2f} across {macro_fit["months"]} complete monthly changes.')
            st.caption('Fitted using the full loaded price history, independently of the selected chart window. Association does not establish causation.')
        else:
            st.info('Yield sensitivity needs at least 12 matched, complete monthly changes.')
    else:
        st.info('Load economic data to see indicator charts and estimate historical yield sensitivity.')

with tabs[4]:
    st.subheader('What-if sensitivity')
    st.caption('A linear sensitivity exercise, not a forecast. Market and yield associations are estimated separately; combining them can double-count overlapping effects.')
    market_shock=st.slider('Hypothetical benchmark change (%)',-20,20,-5)
    yield_shock=st.slider('Hypothetical 10-year yield change (basis points)',-200,200,0,25,disabled=macro_fit is None)
    try:
        effect=scenario_effect(metrics['beta'],market_shock,macro_fit,yield_shock)
        st.metric('Illustrative combined price change',f'{effect["combined"]:+.2%}',f'{effect["combined"]:+.2%}',delta_color='normal')
        st.caption(f'Market contribution: {effect["market_effect"]:+.2%}; yield contribution: {effect["yield_effect"]:+.2%}. No investment amount or trade is assumed.')
    except ValueError as exc:
        st.info(str(exc))
    st.divider()
    st.subheader('Take the research with you')
    st.write('Export an executive snapshot with embedded chart images, risk drivers, unusual movements, and source notes.')
    if st.button('Prepare HTML report'):
        st.session_state.report=export_report(ticker,benchmark_name,prices,benchmark,metrics,signals,risk,meta,D['financials'],macro_fit)
        st.session_state.report_name=f'{ticker}_risk_report.html'
    if 'report' in st.session_state:
        st.download_button('Download prepared HTML snapshot',st.session_state.report,file_name=st.session_state.report_name,mime='text/html')
        st.caption('The download is the snapshot from when you selected Prepare HTML report. Prepare again after changing your analysis.')
    with st.expander('Methods and limitations'):
        st.markdown('''- Returns use closing prices; provider OHLC is split/dividend adjusted. CSV adjustment is declared by its uploader.
- Volatility uses sample standard deviation and 252 trading observations per year. Assets with different calendars need a different convention.
- Drawdown is measured relative to the running peak within the selected window.
- Beta aligns prices before calculating returns and needs at least 30 matched return intervals.
- Risk index weights: market variability 40%, benchmark sensitivity 15%, unusual moves 15%, balance-sheet leverage 15%, yield sensitivity 15%. Missing inputs reduce coverage; they never become zero-risk values.
- Thresholds are illustrative. The index is not a validated prediction model or an investment recommendation.
- Latest annual SEC figures and revised FRED observations are unsuitable for point-in-time backtesting without additional archival data.''')
    st.caption(f'Source: {meta["source"]} · Retrieved: {meta.get("retrieved_utc","Not supplied")} · Cached: {meta.get("cached",False)}')
