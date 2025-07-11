"""
Risk Management Agent for the Multi-Agent AI Trading System
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from scipy import stats
import math

from src.agents.base_agent import BaseAgent, AnalysisResult, MarketContext
from src.models.trading import AgentType, TradeAction, Portfolio, Position
from src.integrations.openai.client import ModelType
from src.integrations.openai.functions import TradingFunctions, FunctionCategory
from src.utils.logging import get_agent_logger


class RiskMetrics:
    """Risk calculation utilities"""
    
    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        return float(np.percentile(returns_array, (1 - confidence_level) * 100))
    
    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        var = RiskMetrics.calculate_var(returns, confidence_level)
        returns_array = np.array(returns)
        tail_returns = returns_array[returns_array <= var]
        
        return float(np.mean(tail_returns)) if len(tail_returns) > 0 else var
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> float:
        """Calculate Maximum Drawdown"""
        if not prices or len(prices) < 2:
            return 0.0
        
        prices_array = np.array(prices)
        peak = np.maximum.accumulate(prices_array)
        drawdown = (prices_array - peak) / peak
        
        return float(np.min(drawdown))
    
    @staticmethod
    def calculate_volatility(returns: List[float], annualized: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        vol = float(np.std(returns))
        
        if annualized:
            vol *= np.sqrt(252)  # Annualize assuming 252 trading days
        
        return vol
    
    @staticmethod
    def calculate_beta(asset_returns: List[float], market_returns: List[float]) -> float:
        """Calculate Beta relative to market"""
        if not asset_returns or not market_returns or len(asset_returns) != len(market_returns):
            return 1.0
        
        if len(asset_returns) < 2:
            return 1.0
        
        covariance = np.cov(asset_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 1.0
        
        return float(covariance / market_variance)
    
    @staticmethod
    def calculate_correlation_matrix(returns_dict: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix for multiple assets"""
        if not returns_dict:
            return {}
        
        symbols = list(returns_dict.keys())
        correlation_matrix = {}
        
        for symbol1 in symbols:
            correlation_matrix[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    returns1 = returns_dict[symbol1]
                    returns2 = returns_dict[symbol2]
                    
                    if len(returns1) == len(returns2) and len(returns1) > 1:
                        corr = float(np.corrcoef(returns1, returns2)[0][1])
                        correlation_matrix[symbol1][symbol2] = corr if not np.isnan(corr) else 0.0
                    else:
                        correlation_matrix[symbol1][symbol2] = 0.0
        
        return correlation_matrix


class PositionSizing:
    """Position sizing utilities"""
    
    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for position sizing"""
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        b = avg_win / abs(avg_loss)  # Win/loss ratio
        p = win_rate  # Probability of winning
        q = 1 - p  # Probability of losing
        
        kelly_fraction = (b * p - q) / b
        
        # Cap at 25% for safety
        return max(0.0, min(0.25, kelly_fraction))
    
    @staticmethod
    def fixed_fractional(portfolio_value: float, risk_per_trade: float, 
                        entry_price: float, stop_loss: float) -> int:
        """Calculate position size using fixed fractional method"""
        if stop_loss <= 0 or entry_price <= 0 or risk_per_trade <= 0:
            return 0
        
        risk_amount = portfolio_value * risk_per_trade
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return 0
        
        position_size = int(risk_amount / risk_per_share)
        return max(0, position_size)
    
    @staticmethod
    def volatility_adjusted(portfolio_value: float, target_volatility: float,
                          asset_volatility: float, price: float) -> int:
        """Calculate position size based on volatility targeting"""
        if asset_volatility <= 0 or price <= 0 or target_volatility <= 0:
            return 0
        
        volatility_ratio = target_volatility / asset_volatility
        position_value = portfolio_value * volatility_ratio
        
        return int(position_value / price)


class RiskManagementAgent(BaseAgent):
    """Risk Management Agent for portfolio risk assessment and management"""
    
    def __init__(self):
        super().__init__(AgentType.RISK, "risk_management_agent")
        self.risk_metrics = RiskMetrics()
        self.position_sizing = PositionSizing()
        
        # Risk management configuration
        self.max_portfolio_var = 0.05  # 5% daily VaR limit
        self.max_position_size = 0.10  # 10% max position size
        self.max_sector_exposure = 0.30  # 30% max sector exposure
        self.max_correlation = 0.70  # 70% max correlation between positions
        
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="initialization",
            result={"status": "Risk Management Agent initialized"}
        )
    
    def _initialize_agent(self):
        """Initialize risk management specific components"""
        self.risk_cache = {}
        self.portfolio_history = {}
        
        # Risk thresholds by asset class
        self.asset_class_limits = {
            "equity": {"max_weight": 0.80, "max_var": 0.06},
            "bond": {"max_weight": 0.40, "max_var": 0.03},
            "commodity": {"max_weight": 0.20, "max_var": 0.08},
            "crypto": {"max_weight": 0.10, "max_var": 0.15}
        }
    
    def get_system_prompt(self) -> str:
        """Get system prompt for risk management"""
        return """You are a Risk Management Agent specializing in portfolio risk assessment, position sizing, and risk control.

Your responsibilities:
1. Assess portfolio-level risk metrics (VaR, CVaR, Sharpe ratio, max drawdown)
2. Monitor position sizes and concentration risk
3. Calculate optimal position sizes for new trades
4. Identify correlation risks and sector concentration
5. Provide risk-adjusted trading recommendations
6. Monitor compliance with risk limits and guidelines
7. Stress test portfolios under various scenarios

Key principles:
- Preserve capital as the primary objective
- Maintain diversification across assets and sectors
- Use appropriate position sizing based on risk tolerance
- Monitor and limit downside risk exposure
- Consider correlation and concentration risks
- Implement stop-loss and risk management rules
- Adapt risk parameters based on market conditions

Always provide:
- Clear recommendation (buy/sell/hold) with risk considerations
- Confidence level (0.0 to 1.0)
- Detailed risk assessment and reasoning
- Position sizing recommendations
- Risk metrics and compliance status
- Risk mitigation suggestions"""
    
    def get_analysis_functions(self) -> List[Dict[str, Any]]:
        """Get risk management function definitions"""
        return TradingFunctions.get_functions_by_category(FunctionCategory.RISK_MANAGEMENT)
    
    async def analyze(self, context: MarketContext) -> AnalysisResult:
        """Perform risk analysis on market context"""
        try:
            # Get portfolio data (mock for demonstration)
            portfolio_data = await self._get_portfolio_data()
            
            # Calculate portfolio risk metrics
            portfolio_risk = await self._calculate_portfolio_risk(portfolio_data)
            
            # Assess position-specific risk
            position_risk = await self._assess_position_risk(context, portfolio_data)
            
            # Calculate optimal position size
            position_sizing = await self._calculate_position_sizing(context, portfolio_data)
            
            # Check risk limits and compliance
            compliance = await self._check_risk_compliance(portfolio_risk, position_risk)
            
            # Generate analysis prompt
            analysis_prompt = self._create_analysis_prompt(context, portfolio_risk, position_risk, 
                                                         position_sizing, compliance)
            
            # Query OpenAI for analysis
            messages = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.query_openai(messages, ModelType.GPT_4_TURBO)
            
            # Parse response
            if response["type"] == "function_call":
                result = self.parse_function_response(response)
                
                # Add risk data to analysis
                result.analysis_data.update({
                    "portfolio_risk": portfolio_risk,
                    "position_risk": position_risk,
                    "position_sizing": position_sizing,
                    "compliance": compliance,
                    "risk_summary": self._create_risk_summary(portfolio_risk, compliance)
                })
                
                # Validate result
                if self.validate_analysis_result(result):
                    return result
                else:
                    return self._create_fallback_result(context, portfolio_risk)
            else:
                return self._parse_text_response(context, response["content"], portfolio_risk)
                
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol, "context": "risk_analysis"})
            return self._create_error_result(context)
    
    async def _get_portfolio_data(self) -> Dict[str, Any]:
        """Get portfolio data (mock for demonstration)"""
        # In a real implementation, this would fetch from the database
        return {
            "total_value": 1000000.0,  # $1M portfolio
            "cash": 100000.0,  # $100K cash
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 1000,
                    "current_price": 150.0,
                    "market_value": 150000.0,
                    "weight": 0.15,
                    "sector": "technology"
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 500,
                    "current_price": 120.0,
                    "market_value": 60000.0,
                    "weight": 0.06,
                    "sector": "technology"
                },
                {
                    "symbol": "JPM",
                    "quantity": 800,
                    "current_price": 140.0,
                    "market_value": 112000.0,
                    "weight": 0.112,
                    "sector": "financials"
                }
            ],
            "sector_exposure": {
                "technology": 0.21,
                "financials": 0.112,
                "healthcare": 0.08,
                "consumer": 0.05
            },
            "historical_returns": [0.01, -0.02, 0.015, -0.008, 0.022, -0.01, 0.018],  # Last 7 days
            "benchmark_returns": [0.008, -0.015, 0.012, -0.005, 0.018, -0.008, 0.015]  # Market returns
        }
    
    async def _calculate_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive portfolio risk metrics"""
        returns = portfolio_data.get("historical_returns", [])
        benchmark_returns = portfolio_data.get("benchmark_returns", [])
        
        risk_metrics = {}
        
        # VaR and CVaR
        risk_metrics["var_95"] = self.risk_metrics.calculate_var(returns, 0.95)
        risk_metrics["var_99"] = self.risk_metrics.calculate_var(returns, 0.99)
        risk_metrics["cvar_95"] = self.risk_metrics.calculate_cvar(returns, 0.95)
        
        # Performance metrics
        risk_metrics["sharpe_ratio"] = self.risk_metrics.calculate_sharpe_ratio(returns)
        risk_metrics["volatility"] = self.risk_metrics.calculate_volatility(returns)
        
        # Beta calculation
        risk_metrics["beta"] = self.risk_metrics.calculate_beta(returns, benchmark_returns)
        
        # Portfolio concentration
        positions = portfolio_data.get("positions", [])
        weights = [pos["weight"] for pos in positions]
        
        if weights:
            # Herfindahl-Hirschman Index for concentration
            risk_metrics["concentration_index"] = sum(w**2 for w in weights)
            risk_metrics["max_position_weight"] = max(weights)
        else:
            risk_metrics["concentration_index"] = 0.0
            risk_metrics["max_position_weight"] = 0.0
        
        # Sector concentration
        sector_exposure = portfolio_data.get("sector_exposure", {})
        if sector_exposure:
            risk_metrics["max_sector_exposure"] = max(sector_exposure.values())
            risk_metrics["sector_concentration"] = sum(exp**2 for exp in sector_exposure.values())
        else:
            risk_metrics["max_sector_exposure"] = 0.0
            risk_metrics["sector_concentration"] = 0.0
        
        return risk_metrics
    
    async def _assess_position_risk(self, context: MarketContext, 
                                  portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a specific position"""
        symbol = context.symbol
        current_price = context.current_price
        
        # Find existing position if any
        existing_position = None
        for pos in portfolio_data.get("positions", []):
            if pos["symbol"] == symbol:
                existing_position = pos
                break
        
        # Calculate position-specific metrics
        position_risk = {
            "symbol": symbol,
            "current_price": current_price,
            "existing_position": existing_position is not None,
            "current_weight": existing_position["weight"] if existing_position else 0.0,
            "current_value": existing_position["market_value"] if existing_position else 0.0
        }
        
        # Estimate volatility from price history
        if context.price_history:
            prices = [float(candle.get("close", 0)) for candle in context.price_history]
            returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
            position_risk["volatility"] = self.risk_metrics.calculate_volatility(returns)
            position_risk["max_drawdown"] = self.risk_metrics.calculate_max_drawdown(prices)
        else:
            position_risk["volatility"] = 0.20  # Default 20% volatility
            position_risk["max_drawdown"] = 0.0
        
        # Risk rating
        volatility = position_risk["volatility"]
        if volatility > 0.40:
            position_risk["risk_rating"] = "high"
        elif volatility > 0.25:
            position_risk["risk_rating"] = "medium"
        else:
            position_risk["risk_rating"] = "low"
        
        return position_risk
    
    async def _calculate_position_sizing(self, context: MarketContext, 
                                       portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal position sizing"""
        portfolio_value = portfolio_data["total_value"]
        current_price = context.current_price
        
        # Default risk parameters
        risk_per_trade = 0.02  # 2% risk per trade
        stop_loss_pct = 0.05  # 5% stop loss
        target_volatility = 0.15  # 15% target volatility
        
        # Calculate stop loss price
        stop_loss_price = current_price * (1 - stop_loss_pct)
        
        # Fixed fractional sizing
        fixed_fractional_size = self.position_sizing.fixed_fractional(
            portfolio_value, risk_per_trade, current_price, stop_loss_price
        )
        
        # Volatility-adjusted sizing
        asset_volatility = 0.20  # Default volatility estimate
        if context.price_history:
            prices = [float(candle.get("close", 0)) for candle in context.price_history]
            returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
            asset_volatility = self.risk_metrics.calculate_volatility(returns)
        
        volatility_adjusted_size = self.position_sizing.volatility_adjusted(
            portfolio_value, target_volatility, asset_volatility, current_price
        )
        
        # Kelly criterion (simplified)
        kelly_size = int(portfolio_value * 0.05 / current_price)  # Conservative 5% Kelly
        
        # Choose conservative sizing
        recommended_size = min(fixed_fractional_size, volatility_adjusted_size, kelly_size)
        
        # Apply maximum position size limit
        max_position_value = portfolio_value * self.max_position_size
        max_shares = int(max_position_value / current_price)
        recommended_size = min(recommended_size, max_shares)
        
        return {
            "recommended_shares": recommended_size,
            "recommended_value": recommended_size * current_price,
            "recommended_weight": (recommended_size * current_price) / portfolio_value,
            "stop_loss_price": stop_loss_price,
            "risk_amount": abs(current_price - stop_loss_price) * recommended_size,
            "sizing_methods": {
                "fixed_fractional": fixed_fractional_size,
                "volatility_adjusted": volatility_adjusted_size,
                "kelly_criterion": kelly_size,
                "max_allowed": max_shares
            }
        }
    
    async def _check_risk_compliance(self, portfolio_risk: Dict[str, float], 
                                   position_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with risk limits"""
        compliance = {
            "overall_status": "compliant",
            "violations": [],
            "warnings": []
        }
        
        # Check VaR limits
        if abs(portfolio_risk["var_95"]) > self.max_portfolio_var:
            compliance["violations"].append(f"Portfolio VaR ({portfolio_risk['var_95']:.3f}) exceeds limit ({self.max_portfolio_var})")
            compliance["overall_status"] = "violation"
        
        # Check position concentration
        if portfolio_risk["max_position_weight"] > self.max_position_size:
            compliance["violations"].append(f"Position concentration ({portfolio_risk['max_position_weight']:.3f}) exceeds limit ({self.max_position_size})")
            compliance["overall_status"] = "violation"
        
        # Check sector concentration
        if portfolio_risk["max_sector_exposure"] > self.max_sector_exposure:
            compliance["violations"].append(f"Sector exposure ({portfolio_risk['max_sector_exposure']:.3f}) exceeds limit ({self.max_sector_exposure})")
            compliance["overall_status"] = "violation"
        
        # Warnings for approaching limits
        if abs(portfolio_risk["var_95"]) > self.max_portfolio_var * 0.8:
            compliance["warnings"].append("Portfolio VaR approaching limit")
        
        if portfolio_risk["max_position_weight"] > self.max_position_size * 0.8:
            compliance["warnings"].append("Position concentration approaching limit")
        
        return compliance
    
    def _create_analysis_prompt(self, context: MarketContext, portfolio_risk: Dict[str, float],
                              position_risk: Dict[str, Any], position_sizing: Dict[str, Any],
                              compliance: Dict[str, Any]) -> str:
        """Create analysis prompt for OpenAI"""
        current_price = context.current_price
        symbol = context.symbol
        
        prompt = f"""
Perform risk management analysis for {symbol} at current price ${current_price:.2f}

PORTFOLIO RISK METRICS:
- VaR (95%): {portfolio_risk['var_95']:.3f}
- VaR (99%): {portfolio_risk['var_99']:.3f}
- CVaR (95%): {portfolio_risk['cvar_95']:.3f}
- Sharpe Ratio: {portfolio_risk['sharpe_ratio']:.2f}
- Portfolio Volatility: {portfolio_risk['volatility']:.3f}
- Beta: {portfolio_risk['beta']:.2f}
- Concentration Index: {portfolio_risk['concentration_index']:.3f}
- Max Position Weight: {portfolio_risk['max_position_weight']:.3f}
- Max Sector Exposure: {portfolio_risk['max_sector_exposure']:.3f}

POSITION RISK ASSESSMENT:
- Symbol: {position_risk['symbol']}
- Current Weight: {position_risk['current_weight']:.3f}
- Position Volatility: {position_risk['volatility']:.3f}
- Max Drawdown: {position_risk['max_drawdown']:.3f}
- Risk Rating: {position_risk['risk_rating']}
- Existing Position: {position_risk['existing_position']}

POSITION SIZING RECOMMENDATION:
- Recommended Shares: {position_sizing['recommended_shares']}
- Recommended Value: ${position_sizing['recommended_value']:,.0f}
- Recommended Weight: {position_sizing['recommended_weight']:.3f}
- Stop Loss Price: ${position_sizing['stop_loss_price']:.2f}
- Risk Amount: ${position_sizing['risk_amount']:,.0f}

RISK COMPLIANCE:
- Overall Status: {compliance['overall_status']}
- Violations: {len(compliance['violations'])}
- Warnings: {len(compliance['warnings'])}

Based on this risk analysis, provide:
1. Risk-adjusted recommendation (buy/sell/hold)
2. Confidence level (0.0 to 1.0)
3. Detailed risk assessment and reasoning
4. Position sizing recommendations
5. Risk mitigation strategies
6. Compliance considerations

Use the assess_portfolio_risk function to provide your analysis.
"""
        return prompt
    
    def _create_risk_summary(self, portfolio_risk: Dict[str, float], 
                           compliance: Dict[str, Any]) -> Dict[str, str]:
        """Create risk analysis summary"""
        summary = {}
        
        # Overall risk level
        var_95 = abs(portfolio_risk["var_95"])
        if var_95 > 0.05:
            summary["risk_level"] = "High risk - VaR exceeds 5%"
        elif var_95 > 0.03:
            summary["risk_level"] = "Medium risk - VaR between 3-5%"
        else:
            summary["risk_level"] = "Low risk - VaR below 3%"
        
        # Portfolio health
        sharpe = portfolio_risk["sharpe_ratio"]
        if sharpe > 1.5:
            summary["portfolio_health"] = "Excellent risk-adjusted returns"
        elif sharpe > 1.0:
            summary["portfolio_health"] = "Good risk-adjusted returns"
        elif sharpe > 0.5:
            summary["portfolio_health"] = "Moderate risk-adjusted returns"
        else:
            summary["portfolio_health"] = "Poor risk-adjusted returns"
        
        # Compliance status
        summary["compliance"] = f"Risk compliance: {compliance['overall_status']}"
        if compliance["violations"]:
            summary["compliance"] += f" ({len(compliance['violations'])} violations)"
        
        return summary
    
    def _create_fallback_result(self, context: MarketContext, portfolio_risk: Dict[str, float]) -> AnalysisResult:
        """Create fallback result when analysis fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.3,
            reasoning="Risk analysis inconclusive - recommending hold for risk management",
            analysis_data={
                "portfolio_risk": portfolio_risk,
                "fallback": True,
                "error": "Analysis validation failed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _parse_text_response(self, context: MarketContext, content: str,
                           portfolio_risk: Dict[str, float]) -> AnalysisResult:
        """Parse text response when function calling fails"""
        content_lower = content.lower()
        
        # Risk management tends to be more conservative
        if "buy" in content_lower and "risk" not in content_lower:
            recommendation = TradeAction.BUY
            confidence = 0.5  # Lower confidence due to risk considerations
        elif "sell" in content_lower:
            recommendation = TradeAction.SELL
            confidence = 0.6
        else:
            recommendation = TradeAction.HOLD
            confidence = 0.7  # Higher confidence in hold recommendations
        
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=content,
            analysis_data={
                "portfolio_risk": portfolio_risk,
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
            reasoning="Risk analysis failed due to error - defaulting to hold for safety",
            analysis_data={"error": True},
            timestamp=datetime.now(timezone.utc)
        )
    
    def calculate_portfolio_var(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate current portfolio VaR for quick reference"""
        try:
            returns = portfolio_data.get("historical_returns", [])
            return self.risk_metrics.calculate_var(returns, 0.95)
        except Exception as e:
            self.logger.log_error(e, {"context": "portfolio_var_calculation"})
            return 0.0
    
    def get_risk_limits(self) -> Dict[str, float]:
        """Get current risk limits"""
        return {
            "max_portfolio_var": self.max_portfolio_var,
            "max_position_size": self.max_position_size,
            "max_sector_exposure": self.max_sector_exposure,
            "max_correlation": self.max_correlation
        }

