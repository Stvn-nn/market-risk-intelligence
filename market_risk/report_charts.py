"""Script-free chart snapshots for reports and previewers that cannot run Plotly."""
from __future__ import annotations
import base64
from html import escape
from io import BytesIO
from threading import RLock

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

GREEN, RED, BLUE = '#4ade80', '#fb7185', '#83b5ff'
_LOCK = RLock()


def _axis(ax):
    ax.set_facecolor('#101722')
    ax.tick_params(colors='#a4afc0',labelsize=10)
    ax.grid(axis='y',color='#263346',linewidth=.6)
    ax.set_axisbelow(True)
    ax.yaxis.label.set_color('#e5eaf2')
    for spine in ax.spines.values():
        spine.set_color('#263346')


def _png(fig):
    output=BytesIO()
    fig.savefig(output,format='png',dpi=140,facecolor=fig.get_facecolor())
    return output.getvalue()


def price_volume_png(prices,signals,label='Price & volume'):
    """Render the same closing prices, moving averages, flags, and daily volumes."""
    with _LOCK:
        fig=Figure(figsize=(12,6),facecolor='#101722',layout='constrained')
        top,bottom=fig.subplots(2,1,sharex=True,gridspec_kw={'height_ratios':[3,1]})
        for ax in [top,bottom]:
            _axis(ax)
        x=mdates.date2num(prices.index.to_pydatetime())
        close=prices['close'].to_numpy(dtype=float)
        points=np.column_stack([x,close])
        segments=np.stack([points[:-1],points[1:]],axis=1)
        colors=np.where(np.diff(close)>=0,GREEN,RED)
        top.add_collection(LineCollection(segments,colors=colors,linewidths=1.6))
        top.autoscale_view()
        for window,color in [(20,BLUE),(50,'#c4b5fd')]:
            top.plot(x,prices['close'].rolling(window).mean(),color=color,lw=1,ls='--',label=f'{window}-day average')
        flags=signals['flag'].reindex(prices.index,fill_value=False).to_numpy(dtype=bool)
        top.scatter(x[flags],close[flags],marker='D',s=33,facecolors='none',edgecolors='#fbbf24',label='Unusual move',zorder=5)
        top.set_title(label,color='#e5eaf2',loc='left',fontsize=15,pad=16)
        top.set_ylabel('Closing price')
        top.legend(loc='upper left',fontsize=9,facecolor='#101722',edgecolor='#263346',labelcolor='#e5eaf2')
        volume_colors=np.where(prices['close']>=prices['open'],GREEN,RED)
        bottom.bar(x,prices['volume']/1_000_000,width=.85,color=volume_colors,alpha=.8)
        bottom.set_ylabel('Volume (millions)')
        locator=mdates.AutoDateLocator(minticks=4,maxticks=8)
        bottom.xaxis.set_major_locator(locator)
        bottom.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        bottom.get_xaxis().get_offset_text().set_color('#a4afc0')
        top.margins(x=.015)
        bottom.margins(x=.015)
        return _png(fig)


def comparison_png(prices,benchmark,ticker,benchmark_name):
    with _LOCK:
        paired=pd.concat([prices['close'],benchmark['close']],axis=1).dropna()
        fig=Figure(figsize=(12,3.8),facecolor='#101722',layout='constrained')
        ax=fig.subplots()
        _axis(ax)
        for i,name,color,dash in [(0,ticker,BLUE,'-'),(1,benchmark_name,'#c4b5fd','--')]:
            ax.plot(paired.index,paired.iloc[:,i]/paired.iloc[0,i]*100,label=name,color=color,ls=dash,lw=1.5)
        ax.set_ylabel('Index · starting value = 100')
        ax.set_title('Benchmark comparison',color='#e5eaf2',loc='left',fontsize=15,pad=14)
        ax.legend(facecolor='#101722',edgecolor='#263346',labelcolor='#e5eaf2')
        locator=mdates.AutoDateLocator(minticks=4,maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.get_xaxis().get_offset_text().set_color('#a4afc0')
        return _png(fig)


def embedded_png(data,alt):
    encoded=base64.b64encode(data).decode('ascii')
    return f'<img alt="{escape(alt,quote=True)}" src="data:image/png;base64,{encoded}" style="display:block;width:100%;height:auto;border-radius:12px">'
