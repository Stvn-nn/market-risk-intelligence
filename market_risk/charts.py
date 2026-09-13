"""Consistent chart styles. Direction always has a sign or label as well as color."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

GREEN, RED, BLUE, MUTED = '#4ade80', '#fb7185', '#83b5ff', '#a4afc0'


def style(fig, height=410):
    fig.update_layout(template='plotly_dark', paper_bgcolor='#101722',plot_bgcolor='#101722',
                      font=dict(family='Arial, sans-serif',color='#e5eaf2',size=12),height=height,
                      margin=dict(l=12,r=12,t=34,b=24),hovermode='x unified',
                      legend=dict(orientation='h',y=1.13,x=0),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#243043'))
    return fig


def price_chart(prices, signals, kind='Candlestick', averages=True):
    fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.06,row_heights=[.78,.22])
    if kind=='Candlestick':
        fig.add_trace(go.Candlestick(x=prices.index,open=prices.open,high=prices.high,low=prices.low,close=prices.close,
                       increasing_line_color=GREEN,decreasing_line_color=RED,name='Adjusted OHLC'),row=1,col=1)
    else:
        # Draw each daily segment with its actual direction.
        for rising,color,label in [(True,GREEN,'Price · up'),(False,RED,'Price · down')]:
            x,y=[],[]
            for i in range(1,len(prices)):
                if bool(prices.close.iloc[i]>=prices.close.iloc[i-1])==rising:
                    x.extend([prices.index[i-1],prices.index[i],None]); y.extend([prices.close.iloc[i-1],prices.close.iloc[i],None])
            fig.add_trace(go.Scatter(x=x,y=y,mode='lines',line=dict(color=color,width=2),name=label),row=1,col=1)
    if averages:
        for window,color in [(20,BLUE),(50,'#c4b5fd')]:
            fig.add_trace(go.Scatter(x=prices.index,y=prices.close.rolling(window).mean(),name=f'{window}-day average',line=dict(color=color,width=1.3,dash='dot')),row=1,col=1)
    flagged = prices.loc[signals['flag'].reindex(prices.index,fill_value=False)]
    fig.add_trace(go.Scatter(x=flagged.index,y=flagged.close,mode='markers',name='Unusual move',marker=dict(symbol='diamond-open',size=11,color='#fbbf24',line=dict(width=2))),row=1,col=1)
    fig.add_trace(go.Bar(x=prices.index,y=prices.volume,name='Volume',marker_color=np.where(prices.close>=prices.open,GREEN,RED),opacity=.6),row=2,col=1)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text='Price',row=1,col=1)
    fig.update_yaxes(title_text='Volume',row=2,col=1)
    return style(fig,490)


def comparison_chart(prices, benchmark, ticker, benchmark_name):
    paired = pd.concat([prices.close.rename(ticker),benchmark.close.rename(benchmark_name)],axis=1).dropna()
    fig = go.Figure()
    for i in range(len(paired.columns)):
        values = paired.iloc[:,i]/paired.iloc[0,i]*100
        fig.add_trace(go.Scatter(x=paired.index,y=values,name=f'{paired.columns[i]} · rebased',line=dict(color=BLUE if i==0 else '#c4b5fd',dash='solid' if i==0 else 'dash')))
    fig.update_yaxes(title_text='Index · starting value = 100')
    return style(fig,330)


def risk_history(prices):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,subplot_titles=('30-day annualized volatility','Drawdown from running peak'))
    vol = prices.close.pct_change(fill_method=None).rolling(30).std()*np.sqrt(252)*100
    draw = (prices.close/prices.close.cummax()-1)*100
    fig.add_trace(go.Scatter(x=prices.index,y=vol,name='Volatility',line=dict(color=BLUE)),row=1,col=1)
    fig.add_trace(go.Scatter(x=prices.index,y=draw,name='Drawdown',fill='tozeroy',line=dict(color=RED)),row=2,col=1)
    fig.update_yaxes(ticksuffix='%')
    return style(fig,480)
