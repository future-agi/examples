"""
Market Data Provider Integration for the Multi-Agent AI Trading System
"""
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np

# Add Manus API client path
sys.path.append('/opt/.manus/.sandbox-runtime')
from data_api import ApiClient

from config.settings import config
from src.utils.logging import get_component_logger

logger = get_component_logger("market_data")


@dataclass
class MarketDataPoint:
    """Single market data point"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "adjusted_close": self.adjusted_close
        }


@dataclass
class StockInsights:
    """Stock insights and analysis data"""
    symbol: str
    technical_outlook: Dict[str, Any]
    valuation: Dict[str, Any]
    recommendation: Dict[str, Any]
    support_resistance: Dict[str, float]
    company_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "technical_outlook": self.technical_outlook,
            "valuation": self.valuation,
            "recommendation": self.recommendation,
            "support_resistance": self.support_resistance,
            "company_metrics": self.company_metrics
        }


class YahooFinanceProvider:
    """Yahoo Finance data provider using Manus API Hub"""
    
    def __init__(self):
        self.client = ApiClient()
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def get_stock_chart(self, symbol: str, interval: str = "1d", 
                            range_period: str = "1mo") -> List[MarketDataPoint]:
        """Get stock chart data"""
        try:
            await self._rate_limit()
            
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'interval': interval,
                'range': range_period,
                'includeAdjustedClose': True
            })
            
            if not response or 'chart' not in response:
                logger.error(f"Invalid response for {symbol}: {response}")
                return []
            
            chart_data = response['chart']['result'][0] if response['chart']['result'] else None
            if not chart_data:
                logger.error(f"No chart data for {symbol}")
                return []
            
            timestamps = chart_data.get('timestamp', [])
            indicators = chart_data.get('indicators', {})
            quote_data = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
            adjclose_data = indicators.get('adjclose', [{}])[0] if indicators.get('adjclose') else {}
            
            # Extract price data
            opens = quote_data.get('open', [])
            highs = quote_data.get('high', [])
            lows = quote_data.get('low', [])
            closes = quote_data.get('close', [])
            volumes = quote_data.get('volume', [])
            adj_closes = adjclose_data.get('adjclose', [])
            
            market_data = []
            
            for i, timestamp in enumerate(timestamps):
                if (i < len(opens) and i < len(highs) and i < len(lows) and 
                    i < len(closes) and i < len(volumes)):
                    
                    # Skip None values
                    if (opens[i] is None or highs[i] is None or lows[i] is None or 
                        closes[i] is None or volumes[i] is None):
                        continue
                    
                    adj_close = adj_closes[i] if i < len(adj_closes) and adj_closes[i] is not None else None
                    
                    data_point = MarketDataPoint(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                        open=float(opens[i]),
                        high=float(highs[i]),
                        low=float(lows[i]),
                        close=float(closes[i]),
                        volume=int(volumes[i]),
                        adjusted_close=float(adj_close) if adj_close is not None else None
                    )
                    
                    market_data.append(data_point)
            
            logger.info(f"Retrieved {len(market_data)} data points for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching chart data for {symbol}: {e}")
            return []
    
    async def get_stock_insights(self, symbol: str) -> Optional[StockInsights]:
        """Get stock insights and analysis"""
        try:
            await self._rate_limit()
            
            response = self.client.call_api('YahooFinance/get_stock_insights', query={
                'symbol': symbol
            })
            
            if not response or 'finance' not in response:
                logger.error(f"Invalid insights response for {symbol}: {response}")
                return None
            
            result = response['finance']['result']
            if not result:
                logger.error(f"No insights data for {symbol}")
                return None
            
            instrument_info = result.get('instrumentInfo', {})
            
            # Extract technical outlook
            technical_events = instrument_info.get('technicalEvents', {})
            technical_outlook = {
                "short_term": technical_events.get('shortTermOutlook', {}),
                "intermediate_term": technical_events.get('intermediateTermOutlook', {}),
                "long_term": technical_events.get('longTermOutlook', {})
            }
            
            # Extract support/resistance
            key_technicals = instrument_info.get('keyTechnicals', {})
            support_resistance = {
                "support": key_technicals.get('support', 0.0),
                "resistance": key_technicals.get('resistance', 0.0),
                "stop_loss": key_technicals.get('stopLoss', 0.0)
            }
            
            # Extract valuation
            valuation = instrument_info.get('valuation', {})
            
            # Extract recommendation
            recommendation = result.get('recommendation', {})
            
            # Extract company metrics
            company_snapshot = result.get('companySnapshot', {})
            company_metrics = company_snapshot.get('company', {})
            
            insights = StockInsights(
                symbol=symbol,
                technical_outlook=technical_outlook,
                valuation=valuation,
                recommendation=recommendation,
                support_resistance=support_resistance,
                company_metrics=company_metrics
            )
            
            logger.info(f"Retrieved insights for {symbol}")
            return insights
            
        except Exception as e:
            logger.error(f"Error fetching insights for {symbol}: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        try:
            # Get latest 1-day data
            data = await self.get_stock_chart(symbol, interval="1m", range_period="1d")
            
            if data:
                return data[-1].close
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None


class MarketDataProcessor:
    """Process and validate market data"""
    
    def __init__(self):
        self.data_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes cache
    
    def validate_data_point(self, data_point: MarketDataPoint) -> bool:
        """Validate a single data point"""
        try:
            # Check for reasonable price values
            if data_point.open <= 0 or data_point.high <= 0 or data_point.low <= 0 or data_point.close <= 0:
                return False
            
            # Check price relationships
            if data_point.high < data_point.low:
                return False
            
            if (data_point.open > data_point.high or data_point.open < data_point.low or
                data_point.close > data_point.high or data_point.close < data_point.low):
                return False
            
            # Check volume
            if data_point.volume < 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data point: {e}")
            return False
    
    def clean_data(self, data_points: List[MarketDataPoint]) -> List[MarketDataPoint]:
        """Clean and validate market data"""
        cleaned_data = []
        
        for data_point in data_points:
            if self.validate_data_point(data_point):
                cleaned_data.append(data_point)
            else:
                logger.warning(f"Invalid data point removed: {data_point.symbol} at {data_point.timestamp}")
        
        return cleaned_data
    
    def calculate_returns(self, data_points: List[MarketDataPoint]) -> List[float]:
        """Calculate returns from price data"""
        if len(data_points) < 2:
            return []
        
        returns = []
        for i in range(1, len(data_points)):
            prev_price = data_points[i-1].close
            curr_price = data_points[i].close
            
            if prev_price > 0:
                return_value = (curr_price - prev_price) / prev_price
                returns.append(return_value)
        
        return returns
    
    def calculate_technical_indicators(self, data_points: List[MarketDataPoint]) -> Dict[str, float]:
        """Calculate basic technical indicators"""
        if not data_points:
            return {}
        
        closes = [dp.close for dp in data_points]
        highs = [dp.high for dp in data_points]
        lows = [dp.low for dp in data_points]
        volumes = [dp.volume for dp in data_points]
        
        indicators = {}
        
        # Simple Moving Averages
        if len(closes) >= 20:
            indicators["sma_20"] = np.mean(closes[-20:])
        if len(closes) >= 50:
            indicators["sma_50"] = np.mean(closes[-50:])
        
        # Price change
        if len(closes) >= 2:
            indicators["price_change"] = (closes[-1] - closes[-2]) / closes[-2]
        
        # Volume average
        if len(volumes) >= 20:
            indicators["avg_volume"] = np.mean(volumes[-20:])
            indicators["volume_ratio"] = volumes[-1] / indicators["avg_volume"] if indicators["avg_volume"] > 0 else 1.0
        
        # Volatility (20-day)
        if len(closes) >= 20:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            indicators["volatility"] = np.std(returns[-19:]) * np.sqrt(252)  # Annualized
        
        return indicators
    
    def is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache_expiry:
            return False
        
        return datetime.now(timezone.utc) < self.cache_expiry[symbol]
    
    def cache_data(self, symbol: str, data: Any):
        """Cache data with expiry"""
        self.data_cache[symbol] = data
        self.cache_expiry[symbol] = datetime.now(timezone.utc) + timedelta(seconds=self.cache_duration)
    
    def get_cached_data(self, symbol: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self.is_cache_valid(symbol):
            return self.data_cache.get(symbol)
        return None


class MarketDataManager:
    """Main market data manager"""
    
    def __init__(self):
        self.yahoo_provider = YahooFinanceProvider()
        self.processor = MarketDataProcessor()
        
        # Supported symbols for demo
        self.supported_symbols = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM", "JNJ", "V"
        ]
        
        logger.info("Market Data Manager initialized")
    
    async def get_market_data(self, symbol: str, interval: str = "1d", 
                            range_period: str = "1mo") -> List[MarketDataPoint]:
        """Get market data for a symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{interval}_{range_period}"
            cached_data = self.processor.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                return cached_data
            
            # Fetch fresh data
            data = await self.yahoo_provider.get_stock_chart(symbol, interval, range_period)
            
            # Clean and validate data
            cleaned_data = self.processor.clean_data(data)
            
            # Cache the data
            self.processor.cache_data(cache_key, cleaned_data)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return []
    
    async def get_stock_insights(self, symbol: str) -> Optional[StockInsights]:
        """Get stock insights"""
        try:
            # Check cache first
            cache_key = f"{symbol}_insights"
            cached_insights = self.processor.get_cached_data(cache_key)
            if cached_insights:
                logger.info(f"Using cached insights for {symbol}")
                return cached_insights
            
            # Fetch fresh insights
            insights = await self.yahoo_provider.get_stock_insights(symbol)
            
            if insights:
                # Cache the insights
                self.processor.cache_data(cache_key, insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting insights for {symbol}: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        try:
            return await self.yahoo_provider.get_current_price(symbol)
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def get_market_context(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market context for a symbol"""
        try:
            # Get price data
            price_data = await self.get_market_data(symbol, interval="1d", range_period="3mo")
            
            # Get insights
            insights = await self.get_stock_insights(symbol)
            
            # Calculate technical indicators
            technical_indicators = self.processor.calculate_technical_indicators(price_data)
            
            # Calculate returns
            returns = self.processor.calculate_returns(price_data)
            
            # Get current price
            current_price = price_data[-1].close if price_data else None
            
            context = {
                "symbol": symbol,
                "current_price": current_price,
                "price_history": [dp.to_dict() for dp in price_data],
                "volume_data": [{"timestamp": dp.timestamp.isoformat(), "volume": dp.volume} for dp in price_data],
                "market_indicators": technical_indicators,
                "returns": returns,
                "insights": insights.to_dict() if insights else None,
                "data_quality": {
                    "price_points": len(price_data),
                    "data_completeness": len(price_data) / 63 if len(price_data) <= 63 else 1.0,  # 3 months ≈ 63 trading days
                    "last_update": datetime.now(timezone.utc).isoformat()
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting market context for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "current_price": None,
                "price_history": [],
                "volume_data": [],
                "market_indicators": {},
                "returns": [],
                "insights": None
            }
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.supported_symbols.copy()
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is supported and has data"""
        try:
            current_price = await self.get_current_price(symbol)
            return current_price is not None
        except Exception:
            return False


# Global market data manager instance
market_data_manager = MarketDataManager()

