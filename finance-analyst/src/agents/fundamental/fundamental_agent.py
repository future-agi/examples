"""
Fundamental Analysis Agent for the Multi-Agent AI Trading System
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

from src.agents.base_agent import BaseAgent, AnalysisResult, MarketContext
from src.models.trading import AgentType, TradeAction
from src.integrations.openai.client import ModelType
from src.integrations.openai.functions import TradingFunctions, FunctionCategory
from src.utils.logging import get_agent_logger


class FinancialRatios:
    """Financial ratio calculation utilities"""
    
    @staticmethod
    def calculate_pe_ratio(price: float, eps: float) -> float:
        """Calculate Price-to-Earnings ratio"""
        if eps <= 0:
            return float('inf')
        return price / eps
    
    @staticmethod
    def calculate_pb_ratio(price: float, book_value_per_share: float) -> float:
        """Calculate Price-to-Book ratio"""
        if book_value_per_share <= 0:
            return float('inf')
        return price / book_value_per_share
    
    @staticmethod
    def calculate_roe(net_income: float, shareholders_equity: float) -> float:
        """Calculate Return on Equity"""
        if shareholders_equity <= 0:
            return 0.0
        return (net_income / shareholders_equity) * 100
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        """Calculate Return on Assets"""
        if total_assets <= 0:
            return 0.0
        return (net_income / total_assets) * 100
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> float:
        """Calculate Debt-to-Equity ratio"""
        if shareholders_equity <= 0:
            return float('inf')
        return total_debt / shareholders_equity
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
        """Calculate Current Ratio"""
        if current_liabilities <= 0:
            return float('inf')
        return current_assets / current_liabilities
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
        """Calculate Quick Ratio (Acid Test)"""
        if current_liabilities <= 0:
            return float('inf')
        return (current_assets - inventory) / current_liabilities
    
    @staticmethod
    def calculate_gross_margin(gross_profit: float, revenue: float) -> float:
        """Calculate Gross Margin"""
        if revenue <= 0:
            return 0.0
        return (gross_profit / revenue) * 100
    
    @staticmethod
    def calculate_operating_margin(operating_income: float, revenue: float) -> float:
        """Calculate Operating Margin"""
        if revenue <= 0:
            return 0.0
        return (operating_income / revenue) * 100
    
    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> float:
        """Calculate Net Margin"""
        if revenue <= 0:
            return 0.0
        return (net_income / revenue) * 100


class ValuationModels:
    """Valuation model utilities"""
    
    @staticmethod
    def dcf_valuation(free_cash_flows: List[float], terminal_growth_rate: float = 0.02,
                     discount_rate: float = 0.10, shares_outstanding: float = 1.0) -> float:
        """Discounted Cash Flow valuation"""
        if not free_cash_flows or shares_outstanding <= 0:
            return 0.0
        
        # Calculate present value of projected cash flows
        pv_cash_flows = 0.0
        for i, fcf in enumerate(free_cash_flows):
            pv_cash_flows += fcf / ((1 + discount_rate) ** (i + 1))
        
        # Calculate terminal value
        terminal_fcf = free_cash_flows[-1] * (1 + terminal_growth_rate)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** len(free_cash_flows))
        
        # Total enterprise value
        enterprise_value = pv_cash_flows + pv_terminal_value
        
        # Value per share
        return enterprise_value / shares_outstanding
    
    @staticmethod
    def relative_valuation(target_ratio: float, peer_ratios: List[float], 
                          target_metric: float) -> float:
        """Relative valuation using peer multiples"""
        if not peer_ratios or target_metric <= 0:
            return 0.0
        
        # Calculate median peer ratio
        median_peer_ratio = np.median(peer_ratios)
        
        # Apply to target metric
        return median_peer_ratio * target_metric
    
    @staticmethod
    def graham_number(eps: float, book_value_per_share: float) -> float:
        """Benjamin Graham's intrinsic value formula"""
        if eps <= 0 or book_value_per_share <= 0:
            return 0.0
        
        return (22.5 * eps * book_value_per_share) ** 0.5


class FundamentalAnalysisAgent(BaseAgent):
    """Fundamental Analysis Agent for financial and valuation analysis"""
    
    def __init__(self):
        super().__init__(AgentType.FUNDAMENTAL, "fundamental_analysis_agent")
        self.ratios = FinancialRatios()
        self.valuation = ValuationModels()
        
        # Fundamental analysis thresholds
        self.pe_threshold_low = 15
        self.pe_threshold_high = 25
        self.roe_threshold = 15  # 15% ROE threshold
        self.debt_equity_threshold = 0.5
        
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="initialization",
            result={"status": "Fundamental Analysis Agent initialized"}
        )
    
    def _initialize_agent(self):
        """Initialize fundamental analysis specific components"""
        self.financial_cache = {}
        self.sector_benchmarks = {
            "technology": {"pe": 25, "roe": 20, "debt_equity": 0.3},
            "healthcare": {"pe": 20, "roe": 15, "debt_equity": 0.4},
            "financials": {"pe": 12, "roe": 12, "debt_equity": 0.8},
            "consumer": {"pe": 18, "roe": 15, "debt_equity": 0.5},
            "industrials": {"pe": 16, "roe": 12, "debt_equity": 0.6},
            "energy": {"pe": 14, "roe": 10, "debt_equity": 0.7},
            "utilities": {"pe": 15, "roe": 8, "debt_equity": 0.6},
            "materials": {"pe": 14, "roe": 10, "debt_equity": 0.5}
        }
    
    def get_system_prompt(self) -> str:
        """Get system prompt for fundamental analysis"""
        return """You are a Fundamental Analysis Agent specializing in financial statement analysis, valuation, and company fundamentals.

Your responsibilities:
1. Analyze financial statements (income statement, balance sheet, cash flow)
2. Calculate and interpret financial ratios (P/E, P/B, ROE, ROA, Debt/Equity)
3. Perform valuation analysis using DCF, relative valuation, and other methods
4. Assess company's financial health and growth prospects
5. Analyze earnings reports and guidance
6. Compare metrics against industry peers and benchmarks

Key principles:
- Focus on long-term value creation
- Assess financial strength and stability
- Consider growth prospects and competitive position
- Evaluate management quality and capital allocation
- Compare against sector and market benchmarks
- Consider macroeconomic factors affecting the business

Always provide:
- Clear recommendation (buy/sell/hold)
- Confidence level (0.0 to 1.0)
- Detailed reasoning based on financial analysis
- Key financial metrics and ratios
- Valuation assessment (undervalued/fairly valued/overvalued)
- Risk factors and catalysts"""
    
    def get_analysis_functions(self) -> List[Dict[str, Any]]:
        """Get fundamental analysis function definitions"""
        return TradingFunctions.get_functions_by_category(FunctionCategory.FUNDAMENTAL_ANALYSIS)
    
    async def analyze(self, context: MarketContext) -> AnalysisResult:
        """Perform fundamental analysis on market context"""
        try:
            # Extract fundamental data
            fundamental_data = context.fundamental_data
            if not fundamental_data:
                # Create mock fundamental data for demonstration
                fundamental_data = await self._get_mock_fundamental_data(context.symbol)
            
            # Calculate financial ratios
            ratios = await self._calculate_financial_ratios(context, fundamental_data)
            
            # Perform valuation analysis
            valuation = await self._perform_valuation_analysis(context, fundamental_data, ratios)
            
            # Analyze financial health
            health_score = await self._assess_financial_health(ratios, fundamental_data)
            
            # Generate analysis prompt
            analysis_prompt = self._create_analysis_prompt(context, ratios, valuation, health_score)
            
            # Query OpenAI for analysis
            messages = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.query_openai(messages, ModelType.GPT_4_TURBO)
            
            # Parse response
            if response["type"] == "function_call":
                result = self.parse_function_response(response)
                
                # Add fundamental data to analysis
                result.analysis_data.update({
                    "ratios": ratios,
                    "valuation": valuation,
                    "health_score": health_score,
                    "fundamental_summary": self._create_fundamental_summary(ratios, valuation, health_score)
                })
                
                # Validate result
                if self.validate_analysis_result(result):
                    return result
                else:
                    return self._create_fallback_result(context, ratios)
            else:
                return self._parse_text_response(context, response["content"], ratios, valuation)
                
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol, "context": "fundamental_analysis"})
            return self._create_error_result(context)
    
    async def _get_mock_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Get mock fundamental data for demonstration"""
        # In a real implementation, this would fetch from financial data APIs
        return {
            "revenue": 100000000,  # $100M
            "net_income": 15000000,  # $15M
            "total_assets": 200000000,  # $200M
            "shareholders_equity": 120000000,  # $120M
            "total_debt": 50000000,  # $50M
            "current_assets": 80000000,  # $80M
            "current_liabilities": 40000000,  # $40M
            "inventory": 20000000,  # $20M
            "shares_outstanding": 10000000,  # 10M shares
            "book_value_per_share": 12.0,
            "eps": 1.50,
            "free_cash_flow": 18000000,  # $18M
            "gross_profit": 60000000,  # $60M
            "operating_income": 25000000,  # $25M
            "sector": "technology"
        }
    
    async def _calculate_financial_ratios(self, context: MarketContext, 
                                        fundamental_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all financial ratios"""
        ratios = {}
        
        current_price = context.current_price
        
        # Valuation ratios
        ratios["pe_ratio"] = self.ratios.calculate_pe_ratio(
            current_price, fundamental_data.get("eps", 0)
        )
        ratios["pb_ratio"] = self.ratios.calculate_pb_ratio(
            current_price, fundamental_data.get("book_value_per_share", 0)
        )
        
        # Profitability ratios
        ratios["roe"] = self.ratios.calculate_roe(
            fundamental_data.get("net_income", 0),
            fundamental_data.get("shareholders_equity", 0)
        )
        ratios["roa"] = self.ratios.calculate_roa(
            fundamental_data.get("net_income", 0),
            fundamental_data.get("total_assets", 0)
        )
        
        # Leverage ratios
        ratios["debt_to_equity"] = self.ratios.calculate_debt_to_equity(
            fundamental_data.get("total_debt", 0),
            fundamental_data.get("shareholders_equity", 0)
        )
        
        # Liquidity ratios
        ratios["current_ratio"] = self.ratios.calculate_current_ratio(
            fundamental_data.get("current_assets", 0),
            fundamental_data.get("current_liabilities", 0)
        )
        ratios["quick_ratio"] = self.ratios.calculate_quick_ratio(
            fundamental_data.get("current_assets", 0),
            fundamental_data.get("inventory", 0),
            fundamental_data.get("current_liabilities", 0)
        )
        
        # Margin ratios
        ratios["gross_margin"] = self.ratios.calculate_gross_margin(
            fundamental_data.get("gross_profit", 0),
            fundamental_data.get("revenue", 0)
        )
        ratios["operating_margin"] = self.ratios.calculate_operating_margin(
            fundamental_data.get("operating_income", 0),
            fundamental_data.get("revenue", 0)
        )
        ratios["net_margin"] = self.ratios.calculate_net_margin(
            fundamental_data.get("net_income", 0),
            fundamental_data.get("revenue", 0)
        )
        
        return ratios
    
    async def _perform_valuation_analysis(self, context: MarketContext, 
                                        fundamental_data: Dict[str, Any],
                                        ratios: Dict[str, float]) -> Dict[str, Any]:
        """Perform comprehensive valuation analysis"""
        valuation = {}
        
        current_price = context.current_price
        
        # Graham Number (intrinsic value)
        graham_value = self.valuation.graham_number(
            fundamental_data.get("eps", 0),
            fundamental_data.get("book_value_per_share", 0)
        )
        valuation["graham_number"] = graham_value
        valuation["graham_discount"] = (current_price - graham_value) / graham_value if graham_value > 0 else 0
        
        # Simple DCF (using current FCF and growth assumptions)
        fcf = fundamental_data.get("free_cash_flow", 0)
        shares = fundamental_data.get("shares_outstanding", 1)
        
        if fcf > 0 and shares > 0:
            # Project 5 years of FCF with 5% growth
            projected_fcf = [fcf * (1.05 ** i) for i in range(1, 6)]
            dcf_value = self.valuation.dcf_valuation(projected_fcf, 0.02, 0.10, shares)
            valuation["dcf_value"] = dcf_value
            valuation["dcf_discount"] = (current_price - dcf_value) / dcf_value if dcf_value > 0 else 0
        else:
            valuation["dcf_value"] = 0
            valuation["dcf_discount"] = 0
        
        # Sector comparison
        sector = fundamental_data.get("sector", "technology")
        sector_benchmarks = self.sector_benchmarks.get(sector, self.sector_benchmarks["technology"])
        
        valuation["sector_pe_comparison"] = ratios["pe_ratio"] / sector_benchmarks["pe"] if sector_benchmarks["pe"] > 0 else 1
        valuation["sector_roe_comparison"] = ratios["roe"] / sector_benchmarks["roe"] if sector_benchmarks["roe"] > 0 else 1
        
        # Overall valuation assessment
        discount_factors = [
            valuation["graham_discount"],
            valuation["dcf_discount"]
        ]
        
        avg_discount = np.mean([d for d in discount_factors if abs(d) < 2])  # Filter extreme values
        
        if avg_discount < -0.2:  # 20% undervalued
            valuation["assessment"] = "undervalued"
        elif avg_discount > 0.2:  # 20% overvalued
            valuation["assessment"] = "overvalued"
        else:
            valuation["assessment"] = "fairly_valued"
        
        return valuation
    
    async def _assess_financial_health(self, ratios: Dict[str, float], 
                                     fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall financial health"""
        health_score = {}
        
        # Profitability score (0-100)
        profitability_score = 0
        if ratios["roe"] > 15:
            profitability_score += 30
        elif ratios["roe"] > 10:
            profitability_score += 20
        elif ratios["roe"] > 5:
            profitability_score += 10
        
        if ratios["roa"] > 10:
            profitability_score += 20
        elif ratios["roa"] > 5:
            profitability_score += 15
        elif ratios["roa"] > 2:
            profitability_score += 10
        
        if ratios["net_margin"] > 15:
            profitability_score += 25
        elif ratios["net_margin"] > 10:
            profitability_score += 20
        elif ratios["net_margin"] > 5:
            profitability_score += 15
        
        # Liquidity score (0-100)
        liquidity_score = 0
        if ratios["current_ratio"] > 2:
            liquidity_score += 40
        elif ratios["current_ratio"] > 1.5:
            liquidity_score += 30
        elif ratios["current_ratio"] > 1:
            liquidity_score += 20
        
        if ratios["quick_ratio"] > 1.5:
            liquidity_score += 30
        elif ratios["quick_ratio"] > 1:
            liquidity_score += 25
        elif ratios["quick_ratio"] > 0.8:
            liquidity_score += 15
        
        # Leverage score (0-100)
        leverage_score = 100  # Start with perfect score
        if ratios["debt_to_equity"] > 1:
            leverage_score -= 40
        elif ratios["debt_to_equity"] > 0.5:
            leverage_score -= 20
        elif ratios["debt_to_equity"] > 0.3:
            leverage_score -= 10
        
        # Overall health score
        overall_score = (profitability_score + liquidity_score + leverage_score) / 3
        
        health_score["profitability_score"] = profitability_score
        health_score["liquidity_score"] = liquidity_score
        health_score["leverage_score"] = leverage_score
        health_score["overall_score"] = overall_score
        
        # Health rating
        if overall_score >= 80:
            health_score["rating"] = "excellent"
        elif overall_score >= 60:
            health_score["rating"] = "good"
        elif overall_score >= 40:
            health_score["rating"] = "fair"
        else:
            health_score["rating"] = "poor"
        
        return health_score
    
    def _create_analysis_prompt(self, context: MarketContext, ratios: Dict[str, float],
                              valuation: Dict[str, Any], health_score: Dict[str, Any]) -> str:
        """Create analysis prompt for OpenAI"""
        current_price = context.current_price
        symbol = context.symbol
        
        prompt = f"""
Perform fundamental analysis for {symbol} at current price ${current_price:.2f}

FINANCIAL RATIOS:
- P/E Ratio: {ratios['pe_ratio']:.2f}
- P/B Ratio: {ratios['pb_ratio']:.2f}
- ROE: {ratios['roe']:.2f}%
- ROA: {ratios['roa']:.2f}%
- Debt/Equity: {ratios['debt_to_equity']:.2f}
- Current Ratio: {ratios['current_ratio']:.2f}
- Quick Ratio: {ratios['quick_ratio']:.2f}
- Gross Margin: {ratios['gross_margin']:.2f}%
- Operating Margin: {ratios['operating_margin']:.2f}%
- Net Margin: {ratios['net_margin']:.2f}%

VALUATION ANALYSIS:
- Graham Number: ${valuation['graham_number']:.2f} (Discount: {valuation['graham_discount']:.1%})
- DCF Value: ${valuation['dcf_value']:.2f} (Discount: {valuation['dcf_discount']:.1%})
- Valuation Assessment: {valuation['assessment']}
- Sector P/E Comparison: {valuation['sector_pe_comparison']:.2f}x
- Sector ROE Comparison: {valuation['sector_roe_comparison']:.2f}x

FINANCIAL HEALTH:
- Overall Health Score: {health_score['overall_score']:.1f}/100 ({health_score['rating']})
- Profitability Score: {health_score['profitability_score']:.1f}/100
- Liquidity Score: {health_score['liquidity_score']:.1f}/100
- Leverage Score: {health_score['leverage_score']:.1f}/100

Based on this fundamental analysis, provide:
1. Trading recommendation (buy/sell/hold)
2. Confidence level (0.0 to 1.0)
3. Detailed reasoning based on financial metrics
4. Valuation assessment
5. Key strengths and weaknesses
6. Risk factors and catalysts

Use the analyze_financial_ratios function to provide your analysis.
"""
        return prompt
    
    def _create_fundamental_summary(self, ratios: Dict[str, float], valuation: Dict[str, Any],
                                  health_score: Dict[str, Any]) -> Dict[str, str]:
        """Create fundamental analysis summary"""
        summary = {}
        
        # Valuation summary
        summary["valuation"] = f"{valuation['assessment'].title()} - {valuation['graham_discount']:.1%} vs Graham Number"
        
        # Profitability summary
        if ratios["roe"] > 15:
            summary["profitability"] = f"Strong profitability - ROE {ratios['roe']:.1f}%"
        elif ratios["roe"] > 10:
            summary["profitability"] = f"Good profitability - ROE {ratios['roe']:.1f}%"
        else:
            summary["profitability"] = f"Weak profitability - ROE {ratios['roe']:.1f}%"
        
        # Financial health summary
        summary["health"] = f"{health_score['rating'].title()} financial health ({health_score['overall_score']:.0f}/100)"
        
        # Leverage summary
        if ratios["debt_to_equity"] < 0.3:
            summary["leverage"] = "Conservative debt levels"
        elif ratios["debt_to_equity"] < 0.7:
            summary["leverage"] = "Moderate debt levels"
        else:
            summary["leverage"] = "High debt levels"
        
        return summary
    
    def _create_fallback_result(self, context: MarketContext, ratios: Dict[str, float]) -> AnalysisResult:
        """Create fallback result when analysis fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.3,
            reasoning="Fundamental analysis inconclusive - recommending hold position",
            analysis_data={
                "ratios": ratios,
                "fallback": True,
                "error": "Analysis validation failed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _parse_text_response(self, context: MarketContext, content: str,
                           ratios: Dict[str, float], valuation: Dict[str, Any]) -> AnalysisResult:
        """Parse text response when function calling fails"""
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
                "ratios": ratios,
                "valuation": valuation,
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
            reasoning="Fundamental analysis failed due to error - defaulting to hold",
            analysis_data={"error": True},
            timestamp=datetime.now(timezone.utc)
        )
    
    def get_financial_health_score(self, context: MarketContext) -> Dict[str, Any]:
        """Get financial health score for quick reference"""
        try:
            fundamental_data = context.fundamental_data or self._get_mock_fundamental_data(context.symbol)
            ratios = self._calculate_financial_ratios(context, fundamental_data)
            health_score = self._assess_financial_health(ratios, fundamental_data)
            
            return health_score
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol})
            return {"error": "Failed to calculate financial health score"}

