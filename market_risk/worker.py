"""Isolated market fetch. The parent enforces a hard deadline on this process."""
import json
import sys
import yfinance as yf

if __name__ == '__main__':
    try:
        ticker = yf.Ticker(sys.argv[1])
        prices = ticker.history(period='5y', interval='1d', auto_adjust=True, timeout=10, raise_errors=True)
        if prices.empty:
            raise ValueError('No daily price history returned.')
        prices.index = prices.index.tz_localize(None)
        out = prices[['Open','High','Low','Close','Volume']].reset_index()
        out.columns = ['date','open','high','low','close','volume']
        out['date'] = out['date'].dt.strftime('%Y-%m-%d')
        metadata = ticker.get_history_metadata()
        print(json.dumps({'rows':out.to_dict('records'), 'currency':metadata.get('currency','Unknown'),
                          'exchange':metadata.get('exchangeName','Unknown')}, allow_nan=False))
    except Exception:
        # Provider exception text can contain URLs or credentials. Keep it out of UI/logs.
        print(json.dumps({'error':'No usable history was returned. Check the symbol, network, or provider availability.'}))
        sys.exit(1)
