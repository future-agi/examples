import yfinance as yf
from typing import Dict, Any

class ApiClient:
    """Minimal stub for Manus ApiClient supporting YahooFinance endpoints using yfinance."""

    def call_api(self, endpoint: str, query: Dict[str, Any]) -> Dict[str, Any]:
        if endpoint == 'YahooFinance/get_stock_chart':
            symbol = query.get('symbol')
            interval = query.get('interval', '1d')
            range_period = query.get('range', '1mo')
            include_adj = query.get('includeAdjustedClose', True)

            # yfinance uses period instead of range; we map basic options.
            ticker = yf.Ticker(symbol)
            try:
                hist = ticker.history(period=range_period, interval=interval, auto_adjust=False)
            except Exception:
                return {}

            if hist.empty:
                return {}

            result = {
                'timestamp': [int(ts.timestamp()) for ts in hist.index.tz_localize(None)],
                'indicators': {
                    'quote': [{
                        'open': hist['Open'].fillna(None).tolist(),
                        'high': hist['High'].fillna(None).tolist(),
                        'low': hist['Low'].fillna(None).tolist(),
                        'close': hist['Close'].fillna(None).tolist(),
                        'volume': hist['Volume'].fillna(None).astype(int).tolist(),
                    }]
                }
            }
            if include_adj and 'Adj Close' in hist.columns:
                result['indicators']['adjclose'] = [{
                    'adjclose': hist['Adj Close'].fillna(None).tolist()
                }]

            return {'chart': {'result': [result]}}

        elif endpoint == 'YahooFinance/get_stock_insights':
            # Insights endpoint not implemented; return empty structure.
            return {'finance': {'result': {}}}

        else:
            raise NotImplementedError(f"Endpoint {endpoint} not supported in stub ApiClient") 