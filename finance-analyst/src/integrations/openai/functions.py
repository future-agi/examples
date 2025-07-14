"""
OpenAI function calling framework for trading agents
"""
from typing import Dict, List, Any, Optional
from enum import Enum


class FunctionCategory(Enum):
    """Categories of functions available to agents"""
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_MANAGEMENT = "risk_management"
    MARKET_DATA = "market_data"
    PORTFOLIO_MANAGEMENT = "portfolio_management"


class TradingFunctions:
    """Standard trading functions for OpenAI function calling"""
    
    @staticmethod
    def get_technical_analysis_functions() -> List[Dict[str, Any]]:
        """Get technical analysis function definitions"""
        return [
            {
                "name": "analyze_technical_indicators",
                "description": "Analyze technical indicators for a given symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze"
                        },
                        "indicators": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["RSI", "MACD", "BB", "SMA", "EMA", "STOCH", "ADX"]
                            },
                            "description": "Technical indicators to calculate"
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                            "description": "Timeframe for analysis"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold"],
                            "description": "Trading recommendation based on technical analysis"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the recommendation (0.0 to 1.0)"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the recommendation"
                        },
                        "analysis_data": {
                            "type": "object",
                            "description": "Detailed technical analysis data and calculations"
                        }
                    },
                    "required": ["symbol", "recommendation", "confidence", "reasoning"]
                }
            },
            {
                "name": "identify_chart_patterns",
                "description": "Identify chart patterns in price data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze"
                        },
                        "patterns": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["head_and_shoulders", "double_top", "double_bottom", 
                                        "triangle", "flag", "pennant", "cup_and_handle"]
                            },
                            "description": "Identified chart patterns"
                        },
                        "pattern_strength": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Strength of the identified pattern"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold"],
                            "description": "Trading recommendation based on pattern analysis"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the recommendation"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for pattern identification and recommendation"
                        }
                    },
                    "required": ["symbol", "recommendation", "confidence", "reasoning"]
                }
            }
        ]
    
    @staticmethod
    def get_fundamental_analysis_functions() -> List[Dict[str, Any]]:
        """Get fundamental analysis function definitions"""
        return [
            {
                "name": "analyze_financial_ratios",
                "description": "Analyze financial ratios and company fundamentals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze"
                        },
                        "ratios": {
                            "type": "object",
                            "properties": {
                                "pe_ratio": {"type": "number"},
                                "pb_ratio": {"type": "number"},
                                "roe": {"type": "number"},
                                "roa": {"type": "number"},
                                "debt_to_equity": {"type": "number"},
                                "current_ratio": {"type": "number"},
                                "quick_ratio": {"type": "number"}
                            },
                            "description": "Calculated financial ratios"
                        },
                        "valuation": {
                            "type": "string",
                            "enum": ["undervalued", "fairly_valued", "overvalued"],
                            "description": "Valuation assessment"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold"],
                            "description": "Trading recommendation based on fundamental analysis"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the recommendation"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the valuation and recommendation"
                        },
                        "analysis_data": {
                            "type": "object",
                            "description": "Detailed fundamental analysis data"
                        }
                    },
                    "required": ["symbol", "recommendation", "confidence", "reasoning"]
                }
            },
            {
                "name": "analyze_earnings_report",
                "description": "Analyze earnings report and financial statements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze"
                        },
                        "earnings_surprise": {
                            "type": "number",
                            "description": "Earnings surprise percentage"
                        },
                        "revenue_growth": {
                            "type": "number",
                            "description": "Revenue growth percentage"
                        },
                        "guidance": {
                            "type": "string",
                            "enum": ["raised", "lowered", "maintained", "no_guidance"],
                            "description": "Management guidance update"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold"],
                            "description": "Trading recommendation based on earnings analysis"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the recommendation"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the earnings analysis"
                        }
                    },
                    "required": ["symbol", "recommendation", "confidence", "reasoning"]
                }
            }
        ]
    
    @staticmethod
    def get_sentiment_analysis_functions() -> List[Dict[str, Any]]:
        """Get sentiment analysis function definitions"""
        return [
            {
                "name": "analyze_market_sentiment",
                "description": "Analyze market sentiment from various sources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze"
                        },
                        "news_sentiment": {
                            "type": "number",
                            "minimum": -1.0,
                            "maximum": 1.0,
                            "description": "News sentiment score (-1.0 to 1.0)"
                        },
                        "social_sentiment": {
                            "type": "number",
                            "minimum": -1.0,
                            "maximum": 1.0,
                            "description": "Social media sentiment score (-1.0 to 1.0)"
                        },
                        "analyst_sentiment": {
                            "type": "number",
                            "minimum": -1.0,
                            "maximum": 1.0,
                            "description": "Analyst sentiment score (-1.0 to 1.0)"
                        },
                        "overall_sentiment": {
                            "type": "string",
                            "enum": ["very_negative", "negative", "neutral", "positive", "very_positive"],
                            "description": "Overall sentiment classification"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["buy", "sell", "hold"],
                            "description": "Trading recommendation based on sentiment analysis"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the recommendation"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the sentiment analysis"
                        },
                        "analysis_data": {
                            "type": "object",
                            "description": "Detailed sentiment analysis data and sources"
                        }
                    },
                    "required": ["symbol", "recommendation", "confidence", "reasoning"]
                }
            }
        ]
    
    @staticmethod
    def get_risk_management_functions() -> List[Dict[str, Any]]:
        """Get risk management function definitions"""
        return [
            {
                "name": "assess_portfolio_risk",
                "description": "Assess portfolio risk and recommend adjustments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio_id": {
                            "type": "string",
                            "description": "Portfolio identifier"
                        },
                        "var_95": {
                            "type": "number",
                            "description": "Value at Risk at 95% confidence level"
                        },
                        "max_drawdown": {
                            "type": "number",
                            "description": "Maximum drawdown percentage"
                        },
                        "sharpe_ratio": {
                            "type": "number",
                            "description": "Portfolio Sharpe ratio"
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Overall risk level assessment"
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "symbol": {"type": "string"},
                                    "reason": {"type": "string"}
                                }
                            },
                            "description": "Risk management recommendations"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the risk assessment"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the risk assessment"
                        }
                    },
                    "required": ["portfolio_id", "risk_level", "confidence", "reasoning"]
                }
            },
            {
                "name": "calculate_position_size",
                "description": "Calculate optimal position size for a trade",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol for the trade"
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "Planned entry price"
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price"
                        },
                        "portfolio_value": {
                            "type": "number",
                            "description": "Total portfolio value"
                        },
                        "risk_percentage": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Risk percentage of portfolio (0.0 to 1.0)"
                        },
                        "position_size": {
                            "type": "number",
                            "description": "Calculated position size in shares"
                        },
                        "position_value": {
                            "type": "number",
                            "description": "Calculated position value in dollars"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the position sizing"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reasoning for the position size calculation"
                        }
                    },
                    "required": ["symbol", "position_size", "position_value", "confidence", "reasoning"]
                }
            }
        ]
    
    @staticmethod
    def get_market_data_functions() -> List[Dict[str, Any]]:
        """Get market data function definitions"""
        return [
            {
                "name": "analyze_market_conditions",
                "description": "Analyze overall market conditions and trends",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market_trend": {
                            "type": "string",
                            "enum": ["bullish", "bearish", "sideways"],
                            "description": "Overall market trend"
                        },
                        "volatility": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Market volatility level"
                        },
                        "sector_rotation": {
                            "type": "object",
                            "description": "Sector rotation analysis"
                        },
                        "market_indicators": {
                            "type": "object",
                            "properties": {
                                "vix": {"type": "number"},
                                "spy_trend": {"type": "string"},
                                "yield_curve": {"type": "string"}
                            },
                            "description": "Key market indicators"
                        },
                        "recommendation": {
                            "type": "string",
                            "enum": ["risk_on", "risk_off", "neutral"],
                            "description": "Overall market recommendation"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the market analysis"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the market analysis"
                        }
                    },
                    "required": ["market_trend", "volatility", "recommendation", "confidence", "reasoning"]
                }
            }
        ]
    
    @staticmethod
    def get_all_functions() -> List[Dict[str, Any]]:
        """Get all available functions"""
        all_functions = []
        all_functions.extend(TradingFunctions.get_technical_analysis_functions())
        all_functions.extend(TradingFunctions.get_fundamental_analysis_functions())
        all_functions.extend(TradingFunctions.get_sentiment_analysis_functions())
        all_functions.extend(TradingFunctions.get_risk_management_functions())
        all_functions.extend(TradingFunctions.get_market_data_functions())
        return all_functions
    
    @staticmethod
    def get_functions_by_category(category: FunctionCategory) -> List[Dict[str, Any]]:
        """Get functions by category"""
        function_map = {
            FunctionCategory.TECHNICAL_ANALYSIS: TradingFunctions.get_technical_analysis_functions(),
            FunctionCategory.FUNDAMENTAL_ANALYSIS: TradingFunctions.get_fundamental_analysis_functions(),
            FunctionCategory.SENTIMENT_ANALYSIS: TradingFunctions.get_sentiment_analysis_functions(),
            FunctionCategory.RISK_MANAGEMENT: TradingFunctions.get_risk_management_functions(),
            FunctionCategory.MARKET_DATA: TradingFunctions.get_market_data_functions()
        }
        
        return function_map.get(category, [])
    
    @staticmethod
    def get_function_by_name(function_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific function by name"""
        all_functions = TradingFunctions.get_all_functions()
        for func in all_functions:
            if func["name"] == function_name:
                return func
        return None


class FunctionValidator:
    """Validator for function call responses"""
    
    @staticmethod
    def validate_response(function_name: str, response: Dict[str, Any]) -> bool:
        """Validate function call response"""
        function_def = TradingFunctions.get_function_by_name(function_name)
        if not function_def:
            return False
        
        required_fields = function_def["parameters"].get("required", [])
        
        # Check required fields
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate confidence range
        if "confidence" in response:
            confidence = response["confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                return False
        
        # Validate recommendation enum
        if "recommendation" in response:
            recommendation = response["recommendation"]
            if recommendation not in ["buy", "sell", "hold"]:
                return False
        
        return True
    
    @staticmethod
    def sanitize_response(function_name: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and clean function response"""
        sanitized = response.copy()
        
        # Ensure confidence is in valid range
        if "confidence" in sanitized:
            confidence = sanitized["confidence"]
            if isinstance(confidence, (int, float)):
                sanitized["confidence"] = max(0.0, min(1.0, float(confidence)))
            else:
                sanitized["confidence"] = 0.5
        
        # Ensure recommendation is valid
        if "recommendation" in sanitized:
            recommendation = sanitized["recommendation"].lower()
            if recommendation not in ["buy", "sell", "hold"]:
                sanitized["recommendation"] = "hold"
        
        # Ensure reasoning is provided
        if "reasoning" not in sanitized or not sanitized["reasoning"]:
            sanitized["reasoning"] = "No reasoning provided"
        
        return sanitized

