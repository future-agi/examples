"""
Technical Analysis Agent for the Multi-Agent AI Trading System
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent, AnalysisResult, MarketContext
from src.models.trading import AgentType, TradeAction
from src.integrations.openai.client import ModelType
from src.integrations.openai.functions import TradingFunctions, FunctionCategory
from src.utils.logging import get_agent_logger


class TechnicalIndicators:
    """Technical indicators calculation utilities"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        df = pd.DataFrame({'price': prices})
        delta = df['price'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
        df = pd.DataFrame({'price': prices})
        
        ema_fast = df['price'].ewm(span=fast).mean()
        ema_slow = df['price'].ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            "signal": float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            "histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1] if prices else 0.0
            return {
                "upper": current_price * 1.02,
                "middle": current_price,
                "lower": current_price * 0.98,
                "bandwidth": 0.04
            }
        
        df = pd.DataFrame({'price': prices})
        
        sma = df['price'].rolling(window=period).mean()
        std = df['price'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        bandwidth = (upper_band - lower_band) / sma
        
        return {
            "upper": float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else 0.0,
            "middle": float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0.0,
            "lower": float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else 0.0,
            "bandwidth": float(bandwidth.iloc[-1]) if not pd.isna(bandwidth.iloc[-1]) else 0.0
        }
    
    @staticmethod
    def calculate_moving_averages(prices: List[float], periods: List[int] = [20, 50, 200]) -> Dict[str, float]:
        """Calculate Simple Moving Averages"""
        result = {}
        
        for period in periods:
            if len(prices) >= period:
                sma = np.mean(prices[-period:])
                result[f"sma_{period}"] = float(sma)
            else:
                result[f"sma_{period}"] = prices[-1] if prices else 0.0
        
        return result
    
    @staticmethod
    def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Calculate Stochastic Oscillator"""
        if len(closes) < k_period:
            return {"k": 50.0, "d": 50.0}
        
        df = pd.DataFrame({
            'high': highs,
            'low': lows,
            'close': closes
        })
        
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            "k": float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else 50.0,
            "d": float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else 50.0
        }


class PatternRecognition:
    """Chart pattern recognition utilities"""
    
    @staticmethod
    def detect_support_resistance(prices: List[float], window: int = 10) -> Dict[str, float]:
        """Detect support and resistance levels"""
        if len(prices) < window * 2:
            current_price = prices[-1] if prices else 0.0
            return {
                "support": current_price * 0.95,
                "resistance": current_price * 1.05,
                "strength": 0.5
            }
        
        df = pd.DataFrame({'price': prices})
        
        # Find local minima and maxima
        local_min = df['price'].rolling(window=window, center=True).min() == df['price']
        local_max = df['price'].rolling(window=window, center=True).max() == df['price']
        
        support_levels = df[local_min]['price'].tolist()
        resistance_levels = df[local_max]['price'].tolist()
        
        current_price = prices[-1]
        
        # Find nearest support and resistance
        support = max([p for p in support_levels if p < current_price], default=current_price * 0.95)
        resistance = min([p for p in resistance_levels if p > current_price], default=current_price * 1.05)
        
        # Calculate strength based on number of touches
        support_strength = len([p for p in support_levels if abs(p - support) / support < 0.02])
        resistance_strength = len([p for p in resistance_levels if abs(p - resistance) / resistance < 0.02])
        
        strength = min((support_strength + resistance_strength) / 10.0, 1.0)
        
        return {
            "support": float(support),
            "resistance": float(resistance),
            "strength": float(strength)
        }
    
    @staticmethod
    def detect_trend(prices: List[float], period: int = 20) -> Dict[str, Any]:
        """Detect price trend"""
        if len(prices) < period:
            return {"trend": "sideways", "strength": 0.0, "slope": 0.0}
        
        # Linear regression to determine trend
        x = np.arange(len(prices[-period:]))
        y = np.array(prices[-period:])
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Normalize slope by price
        normalized_slope = slope / np.mean(y)
        
        # Determine trend direction and strength
        if normalized_slope > 0.001:  # 0.1% per period
            trend = "uptrend"
        elif normalized_slope < -0.001:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        strength = min(abs(normalized_slope) * 100, 1.0)
        
        return {
            "trend": trend,
            "strength": float(strength),
            "slope": float(normalized_slope)
        }


class TechnicalAnalysisAgent(BaseAgent):
    """Technical Analysis Agent for chart and indicator analysis"""
    
    def __init__(self):
        super().__init__(AgentType.TECHNICAL, "technical_analysis_agent")
        self.indicators = TechnicalIndicators()
        self.patterns = PatternRecognition()
        
        # Technical analysis configuration
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.bb_squeeze_threshold = 0.1
        
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="initialization",
            result={"status": "Technical Analysis Agent initialized"}
        )
    
    def _initialize_agent(self):
        """Initialize technical analysis specific components"""
        self.analysis_cache = {}
        self.last_analysis_time = {}
    
    def get_system_prompt(self) -> str:
        """Get system prompt for technical analysis"""
        return """You are a Technical Analysis Agent specializing in chart analysis, technical indicators, and price patterns.

Your responsibilities:
1. Analyze price charts and technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
2. Identify chart patterns and support/resistance levels
3. Assess trend strength and momentum
4. Provide buy/sell/hold recommendations based on technical analysis
5. Calculate optimal entry and exit points

Key principles:
- Use multiple indicators for confirmation
- Consider trend direction and momentum
- Identify key support and resistance levels
- Assess risk/reward ratios
- Provide clear reasoning for all recommendations

Always provide:
- Clear recommendation (buy/sell/hold)
- Confidence level (0.0 to 1.0)
- Detailed reasoning based on technical indicators
- Key price levels (support, resistance, targets)
- Risk assessment and stop-loss suggestions"""
    
    def get_analysis_functions(self) -> List[Dict[str, Any]]:
        """Get technical analysis function definitions"""
        return TradingFunctions.get_functions_by_category(FunctionCategory.TECHNICAL_ANALYSIS)
    
    async def analyze(self, context: MarketContext) -> AnalysisResult:
        """Perform technical analysis on market context"""
        try:
            # Extract price data
            price_history = context.price_history
            if not price_history:
                raise ValueError("No price history available for technical analysis")
            
            # Calculate technical indicators
            indicators = await self._calculate_all_indicators(context)
            
            # Detect patterns and trends
            patterns = await self._analyze_patterns(context)
            
            # Generate analysis prompt
            analysis_prompt = self._create_analysis_prompt(context, indicators, patterns)
            
            # Query OpenAI for analysis
            messages = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.query_openai(messages, ModelType.GPT_4_TURBO)
            
            # Parse response
            if response["type"] == "function_call":
                result = self.parse_function_response(response)
                
                # Add technical data to analysis
                result.analysis_data.update({
                    "indicators": indicators,
                    "patterns": patterns,
                    "technical_summary": self._create_technical_summary(indicators, patterns)
                })
                
                # Validate result
                if self.validate_analysis_result(result):
                    return result
                else:
                    # Fallback to conservative recommendation
                    return self._create_fallback_result(context, indicators)
            else:
                # Handle text response
                return self._parse_text_response(context, response["content"], indicators, patterns)
                
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol, "context": "technical_analysis"})
            return self._create_error_result(context)
    
    async def _calculate_all_indicators(self, context: MarketContext) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        price_history = context.price_history
        
        # Extract price arrays
        closes = [float(candle.get("close", 0)) for candle in price_history]
        highs = [float(candle.get("high", 0)) for candle in price_history]
        lows = [float(candle.get("low", 0)) for candle in price_history]
        volumes = [float(candle.get("volume", 0)) for candle in price_history]
        
        indicators = {}
        
        # RSI
        indicators["rsi"] = self.indicators.calculate_rsi(closes)
        
        # MACD
        indicators["macd"] = self.indicators.calculate_macd(closes)
        
        # Bollinger Bands
        indicators["bollinger_bands"] = self.indicators.calculate_bollinger_bands(closes)
        
        # Moving Averages
        indicators["moving_averages"] = self.indicators.calculate_moving_averages(closes)
        
        # Stochastic
        indicators["stochastic"] = self.indicators.calculate_stochastic(highs, lows, closes)
        
        # Volume analysis
        if volumes:
            indicators["volume_sma"] = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            indicators["volume_ratio"] = volumes[-1] / indicators["volume_sma"] if indicators["volume_sma"] > 0 else 1.0
        
        return indicators
    
    async def _analyze_patterns(self, context: MarketContext) -> Dict[str, Any]:
        """Analyze chart patterns"""
        price_history = context.price_history
        closes = [float(candle.get("close", 0)) for candle in price_history]
        
        patterns = {}
        
        # Support and Resistance
        patterns["support_resistance"] = self.patterns.detect_support_resistance(closes)
        
        # Trend Analysis
        patterns["trend"] = self.patterns.detect_trend(closes)
        
        # Price position analysis
        current_price = context.current_price
        sr = patterns["support_resistance"]
        
        patterns["price_position"] = {
            "distance_to_support": (current_price - sr["support"]) / current_price,
            "distance_to_resistance": (sr["resistance"] - current_price) / current_price,
            "position": "middle"
        }
        
        # Determine position
        if patterns["price_position"]["distance_to_support"] < 0.02:
            patterns["price_position"]["position"] = "near_support"
        elif patterns["price_position"]["distance_to_resistance"] < 0.02:
            patterns["price_position"]["position"] = "near_resistance"
        
        return patterns
    
    def _create_analysis_prompt(self, context: MarketContext, indicators: Dict[str, Any], 
                              patterns: Dict[str, Any]) -> str:
        """Create analysis prompt for OpenAI"""
        current_price = context.current_price
        symbol = context.symbol
        
        prompt = f"""
Perform technical analysis for {symbol} at current price ${current_price:.2f}

TECHNICAL INDICATORS:
- RSI: {indicators['rsi']:.2f} (Overbought >70, Oversold <30)
- MACD: {indicators['macd']['macd']:.4f}, Signal: {indicators['macd']['signal']:.4f}, Histogram: {indicators['macd']['histogram']:.4f}
- Bollinger Bands: Upper ${indicators['bollinger_bands']['upper']:.2f}, Middle ${indicators['bollinger_bands']['middle']:.2f}, Lower ${indicators['bollinger_bands']['lower']:.2f}
- Moving Averages: SMA20 ${indicators['moving_averages'].get('sma_20', 0):.2f}, SMA50 ${indicators['moving_averages'].get('sma_50', 0):.2f}
- Stochastic: %K {indicators['stochastic']['k']:.2f}, %D {indicators['stochastic']['d']:.2f}

PATTERN ANALYSIS:
- Trend: {patterns['trend']['trend']} (Strength: {patterns['trend']['strength']:.2f})
- Support Level: ${patterns['support_resistance']['support']:.2f}
- Resistance Level: ${patterns['support_resistance']['resistance']:.2f}
- Price Position: {patterns['price_position']['position']}

VOLUME ANALYSIS:
- Volume Ratio: {indicators.get('volume_ratio', 1.0):.2f} (vs 20-day average)

Based on this technical analysis, provide:
1. Trading recommendation (buy/sell/hold)
2. Confidence level (0.0 to 1.0)
3. Detailed reasoning
4. Key price levels and targets
5. Risk management suggestions

Use the analyze_technical_indicators function to provide your analysis.
"""
        return prompt
    
    def _create_technical_summary(self, indicators: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, str]:
        """Create technical analysis summary"""
        summary = {}
        
        # RSI interpretation
        rsi = indicators["rsi"]
        if rsi > 70:
            summary["rsi_signal"] = "Overbought - potential sell signal"
        elif rsi < 30:
            summary["rsi_signal"] = "Oversold - potential buy signal"
        else:
            summary["rsi_signal"] = "Neutral"
        
        # MACD interpretation
        macd_data = indicators["macd"]
        if macd_data["macd"] > macd_data["signal"]:
            summary["macd_signal"] = "Bullish - MACD above signal line"
        else:
            summary["macd_signal"] = "Bearish - MACD below signal line"
        
        # Trend interpretation
        trend_data = patterns["trend"]
        summary["trend_signal"] = f"{trend_data['trend'].title()} trend with {trend_data['strength']:.1%} strength"
        
        # Support/Resistance
        sr_data = patterns["support_resistance"]
        summary["sr_signal"] = f"Support at ${sr_data['support']:.2f}, Resistance at ${sr_data['resistance']:.2f}"
        
        return summary
    
    def _create_fallback_result(self, context: MarketContext, indicators: Dict[str, Any]) -> AnalysisResult:
        """Create fallback result when analysis fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.3,
            reasoning="Technical analysis inconclusive - recommending hold position",
            analysis_data={
                "indicators": indicators,
                "fallback": True,
                "error": "Analysis validation failed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _parse_text_response(self, context: MarketContext, content: str, 
                           indicators: Dict[str, Any], patterns: Dict[str, Any]) -> AnalysisResult:
        """Parse text response when function calling fails"""
        # Simple text parsing for recommendation
        content_lower = content.lower()
        
        if "buy" in content_lower and "sell" not in content_lower:
            recommendation = TradeAction.BUY
            confidence = 0.6
        elif "sell" in content_lower and "buy" not in content_lower:
            recommendation = TradeAction.SELL
            confidence = 0.6
        else:
            recommendation = TradeAction.HOLD
            confidence = 0.5
        
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=content,
            analysis_data={
                "indicators": indicators,
                "patterns": patterns,
                "response_type": "text_parsed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _create_error_result(self, context: MarketContext) -> AnalysisResult:
        """Create error result when analysis completely fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.1,
            reasoning="Technical analysis failed due to error - defaulting to hold",
            analysis_data={"error": True},
            timestamp=datetime.now(timezone.utc)
        )
    
    def get_indicator_signals(self, context: MarketContext) -> Dict[str, str]:
        """Get current indicator signals for quick reference"""
        try:
            indicators = self._calculate_all_indicators(context)
            patterns = self._analyze_patterns(context)
            
            return self._create_technical_summary(indicators, patterns)
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol})
            return {"error": "Failed to calculate indicator signals"}

