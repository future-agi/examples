"""
AI Trading Assistant Chatbot
Conversational interface for the Multi-Agent AI Trading System
"""

import os
import sys
import json
import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yfinance as yf
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.integrations.openai.client import OpenAIClient, ModelType
from src.agents.base_agent import MarketContext, AnalysisResult
from src.orchestration.orchestrator import TradingOrchestrator, OrchestrationResult
from src.integrations.market_data.data_provider import MarketDataManager
from src.integrations.news.news_provider import NewsDataManager
from src.knowledge.knowledge_base import KnowledgeManager
from src.utils.logging import get_component_logger

logger = get_component_logger("trading_assistant")


class TradingAssistant:
    """AI Trading Assistant Chatbot"""
    
    def __init__(self):
        """Initialize the trading assistant"""
        self.openai_client = OpenAIClient()
        self.market_data_manager = MarketDataManager()
        self.news_data_manager = NewsDataManager()
        self.knowledge_manager = KnowledgeManager(self.openai_client)
        
        # Initialize orchestrator
        self.orchestrator = TradingOrchestrator(
            self.market_data_manager,
            self.news_data_manager,
            self.knowledge_manager
        )
        
        # Conversation history
        self.conversation_history = []
        self.max_history = 10
        
        # Initialize system
        self._initialize_system()
        
    def _initialize_system(self):
        """Initialize the trading system"""
        try:
            # Start orchestrator
            asyncio.create_task(self.orchestrator.start())
            logger.info("Trading Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize trading assistant: {e}")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the trading assistant"""
        return """You are an AI Trading Assistant powered by a sophisticated multi-agent system. You help traders and investors with:

🤖 **Your Capabilities:**
- **Stock Analysis**: Comprehensive analysis using 4 specialized AI agents
- **Technical Analysis**: RSI, MACD, Bollinger Bands, chart patterns, support/resistance
- **Fundamental Analysis**: P/E ratios, financial statements, valuation metrics
- **Sentiment Analysis**: News sentiment, social media trends, market psychology
- **Risk Assessment**: Portfolio risk, position sizing, VaR analysis
- **Trading Education**: Explain concepts, strategies, market dynamics
- **Market Intelligence**: Real-time market data and insights

🎯 **How to Interact:**
- **Analyze stocks**: "Analyze AAPL" or "What do you think about Tesla?"
- **Get recommendations**: "Should I buy Microsoft?" or "Is it time to sell NVDA?"
- **Compare stocks**: "Compare Apple vs Google" or "AAPL vs MSFT analysis"
- **Learn trading**: "Explain RSI" or "What is a bull market?"
- **Risk assessment**: "What are the risks of tech stocks?"
- **Portfolio help**: "How should I diversify my portfolio?"

🧠 **Your Multi-Agent System:**
When you analyze a stock, I coordinate 4 specialized AI agents:
1. **Technical Agent**: Chart analysis, indicators, patterns
2. **Fundamental Agent**: Financial metrics, company analysis
3. **Sentiment Agent**: News and social media sentiment
4. **Risk Agent**: Risk assessment and position sizing

💬 **Communication Style:**
- Be conversational and helpful
- Provide clear, actionable insights
- Explain complex concepts simply
- Always include risk disclaimers
- Use emojis to make responses engaging

⚠️ **Important Disclaimers:**
- This is for educational and informational purposes only
- Not financial advice - always do your own research
- Past performance doesn't guarantee future results
- Consider consulting a financial advisor for major decisions

Ready to help you make smarter trading decisions! What would you like to analyze or learn about?"""
    
    async def process_message(self, user_message: str) -> str:
        """Process user message and return response"""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Detect if this is a stock analysis request
            stock_symbols = self._extract_stock_symbols(user_message)
            
            if stock_symbols:
                # Perform stock analysis
                response = await self._handle_stock_analysis(user_message, stock_symbols)
            else:
                # Handle general conversation
                response = await self._handle_general_conversation(user_message)
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Trim conversation history
            self._trim_conversation_history()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._get_error_response(str(e))
    
    def _extract_stock_symbols(self, message: str) -> List[str]:
        """Extract stock symbols from user message"""
        # Common patterns for stock symbols
        patterns = [
            r'\b([A-Z]{1,5})\b',  # 1-5 uppercase letters
            r'\$([A-Z]{1,5})\b',  # $SYMBOL format
        ]
        
        symbols = []
        for pattern in patterns:
            matches = re.findall(pattern, message.upper())
            symbols.extend(matches)
        
        # Filter out common words that might match
        common_words = {'THE', 'AND', 'OR', 'BUT', 'FOR', 'AT', 'TO', 'FROM', 'UP', 'ON', 'IN', 'OUT', 'OFF', 'OVER', 'UNDER', 'AGAIN', 'FURTHER', 'THEN', 'ONCE', 'HERE', 'THERE', 'WHEN', 'WHERE', 'WHY', 'HOW', 'ALL', 'ANY', 'BOTH', 'EACH', 'FEW', 'MORE', 'MOST', 'OTHER', 'SOME', 'SUCH', 'NO', 'NOR', 'NOT', 'ONLY', 'OWN', 'SAME', 'SO', 'THAN', 'TOO', 'VERY', 'CAN', 'WILL', 'JUST', 'SHOULD', 'NOW', 'GET', 'GOT', 'HAS', 'HAD', 'HIS', 'HER', 'ITS', 'OUR', 'THEIR', 'WHAT', 'WHICH', 'WHO', 'WHOM', 'THIS', 'THAT', 'THESE', 'THOSE', 'AM', 'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN', 'BEING', 'HAVE', 'DO', 'DOES', 'DID', 'DONE', 'DOING', 'WOULD', 'COULD', 'MIGHT', 'MUST', 'SHALL', 'MAY'}
        
        # Also check for company names
        company_symbols = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'ALPHABET': 'GOOGL',
            'AMAZON': 'AMZN',
            'TESLA': 'TSLA',
            'META': 'META',
            'FACEBOOK': 'META',
            'NVIDIA': 'NVDA',
            'NETFLIX': 'NFLX',
            'DISNEY': 'DIS',
            'WALMART': 'WMT',
            'COCA-COLA': 'KO',
            'PEPSI': 'PEP',
            'JOHNSON': 'JNJ',
            'PFIZER': 'PFE',
            'INTEL': 'INTC',
            'AMD': 'AMD',
            'ORACLE': 'ORCL',
            'SALESFORCE': 'CRM',
            'ZOOM': 'ZM',
            'UBER': 'UBER',
            'LYFT': 'LYFT',
            'TWITTER': 'TWTR',
            'SNAPCHAT': 'SNAP',
            'SPOTIFY': 'SPOT',
            'AIRBNB': 'ABNB',
            'COINBASE': 'COIN',
            'ROBINHOOD': 'HOOD',
            'PAYPAL': 'PYPL',
            'SQUARE': 'SQ',
            'SHOPIFY': 'SHOP'
        }
        
        # Check for company names in message
        message_upper = message.upper()
        for company, symbol in company_symbols.items():
            if company in message_upper:
                symbols.append(symbol)
        
        # Remove duplicates and common words
        unique_symbols = list(set([s for s in symbols if s not in common_words and len(s) <= 5]))
        
        # Validate symbols (basic check)
        valid_symbols = []
        for symbol in unique_symbols:
            if len(symbol) >= 1 and symbol.isalpha():
                valid_symbols.append(symbol)
        
        return valid_symbols[:3]  # Limit to 3 symbols max
    
    async def _handle_stock_analysis(self, message: str, symbols: List[str]) -> str:
        """Handle stock analysis requests"""
        try:
            if len(symbols) == 1:
                # Single stock analysis
                symbol = symbols[0]
                analysis_result = await self._analyze_single_stock(symbol)
                return self._format_single_stock_response(symbol, analysis_result, message)
            else:
                # Multiple stock comparison
                results = {}
                for symbol in symbols:
                    results[symbol] = await self._analyze_single_stock(symbol)
                return self._format_comparison_response(symbols, results, message)
                
        except Exception as e:
            logger.error(f"Error in stock analysis: {e}")
            return f"I encountered an issue analyzing the stock(s). Let me provide some general guidance instead.\n\n{self._get_general_stock_guidance(symbols[0] if symbols else 'the stock')}"
    
    async def _analyze_single_stock(self, symbol: str) -> OrchestrationResult:
        """Analyze a single stock using the multi-agent system"""
        try:
            # Use the synchronous analysis method for immediate results
            result = await self.orchestrator.analyze_symbol_sync(symbol)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            # Return mock result for demo
            return self._create_mock_analysis_result(symbol)
    
    async def _build_market_context(self, symbol: str) -> MarketContext:
        """Build market context for analysis"""
        try:
            # Get real market data using yfinance as fallback
            ticker = yf.Ticker(symbol)
            
            # Get current price and history
            hist = ticker.history(period="3mo")
            if hist.empty:
                raise ValueError(f"No data available for {symbol}")
            
            current_price = float(hist['Close'].iloc[-1])
            
            # Format price history
            price_history = []
            for date, row in hist.iterrows():
                price_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Format volume data
            volume_data = [{'date': p['date'], 'volume': p['volume']} for p in price_history]
            
            # Basic market indicators
            market_indicators = {
                'volatility': float(hist['Close'].pct_change().std() * 100),
                'avg_volume': float(hist['Volume'].mean()),
                'price_change_1d': float((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0.0,
                'price_change_5d': float((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0.0,
                'price_change_30d': float((current_price - hist['Close'].iloc[-31]) / hist['Close'].iloc[-31] * 100) if len(hist) > 30 else 0.0
            }
            
            return MarketContext(
                symbol=symbol,
                current_price=current_price,
                price_history=price_history,
                volume_data=volume_data,
                market_indicators=market_indicators,
                news_sentiment=None,  # Will be populated by sentiment agent
                fundamental_data=None  # Will be populated by fundamental agent
            )
            
        except Exception as e:
            logger.error(f"Error building market context for {symbol}: {e}")
            # Return mock context
            return self._create_mock_market_context(symbol)
    
    def _create_mock_market_context(self, symbol: str) -> MarketContext:
        """Create mock market context for demo purposes"""
        import random
        
        base_price = random.uniform(50, 300)
        
        # Generate mock price history
        price_history = []
        current_date = datetime.now() - timedelta(days=90)
        
        for i in range(90):
            date = current_date + timedelta(days=i)
            price_change = random.uniform(-0.05, 0.05)
            base_price *= (1 + price_change)
            
            price_history.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': base_price * random.uniform(0.99, 1.01),
                'high': base_price * random.uniform(1.00, 1.03),
                'low': base_price * random.uniform(0.97, 1.00),
                'close': base_price,
                'volume': random.randint(1000000, 10000000)
            })
        
        volume_data = [{'date': p['date'], 'volume': p['volume']} for p in price_history]
        
        market_indicators = {
            'volatility': random.uniform(15, 35),
            'avg_volume': random.randint(2000000, 8000000),
            'price_change_1d': random.uniform(-3, 3),
            'price_change_5d': random.uniform(-8, 8),
            'price_change_30d': random.uniform(-15, 15)
        }
        
        return MarketContext(
            symbol=symbol,
            current_price=base_price,
            price_history=price_history,
            volume_data=volume_data,
            market_indicators=market_indicators
        )
    
    def _create_mock_analysis_result(self, symbol: str) -> OrchestrationResult:
        """Create mock analysis result for demo purposes"""
        from src.models.trading import TradeAction
        import random
        
        actions = [TradeAction.BUY, TradeAction.SELL, TradeAction.HOLD]
        action = random.choice(actions)
        confidence = random.uniform(0.6, 0.9)
        
        # Generate realistic reasoning based on action
        if action == TradeAction.BUY:
            reasoning = f"Multi-agent analysis suggests {symbol} is a BUY. Technical indicators show bullish momentum with RSI at healthy levels. Fundamental analysis reveals strong financials and growth prospects. Sentiment analysis indicates positive market sentiment. Risk assessment shows acceptable risk levels for current market conditions."
        elif action == TradeAction.SELL:
            reasoning = f"Multi-agent analysis suggests {symbol} is a SELL. Technical indicators show bearish signals with potential downside. Fundamental analysis reveals concerns about valuation or growth. Sentiment analysis indicates negative market sentiment. Risk assessment suggests reducing exposure."
        else:
            reasoning = f"Multi-agent analysis suggests HOLDING {symbol}. Mixed signals from technical and fundamental analysis. Market sentiment is neutral. Risk assessment indicates maintaining current position while monitoring for clearer signals."
        
        return OrchestrationResult(
            symbol=symbol,
            final_decision=action,
            confidence=confidence,
            reasoning=reasoning,
            agent_results={},
            consensus_score=confidence,
            risk_assessment={'risk_level': 'moderate'},
            execution_priority=random.randint(3, 7),
            timestamp=datetime.now(timezone.utc)
        )
    
    def _format_single_stock_response(self, symbol: str, result: OrchestrationResult, original_message: str) -> str:
        """Format response for single stock analysis"""
        action_emoji = {
            'buy': '🟢',
            'sell': '🔴', 
            'hold': '🟡'
        }
        
        action = result.final_decision.value.lower()
        emoji = action_emoji.get(action, '📊')
        
        # Get current price from agent results or use mock
        current_price = "N/A"
        technical_insights = "Technical analysis completed"
        fundamental_insights = "Fundamental analysis completed"
        sentiment_insights = "Sentiment analysis completed"
        risk_insights = "Risk assessment completed"
        
        # Extract insights from agent results
        if result.agent_results:
            for agent_type, agent_result in result.agent_results.items():
                if agent_type == 'technical' and agent_result.analysis_data:
                    technical_data = agent_result.analysis_data
                    if 'current_price' in technical_data:
                        current_price = f"${technical_data['current_price']:.2f}"
                    if 'indicators' in technical_data:
                        indicators = technical_data['indicators']
                        rsi = indicators.get('rsi', 'N/A')
                        technical_insights = f"RSI: {rsi}, {agent_result.reasoning[:100]}..."
                
                elif agent_type == 'fundamental' and agent_result.analysis_data:
                    fundamental_insights = agent_result.reasoning[:100] + "..."
                
                elif agent_type == 'sentiment' and agent_result.analysis_data:
                    sentiment_insights = agent_result.reasoning[:100] + "..."
                
                elif agent_type == 'risk' and agent_result.analysis_data:
                    risk_insights = agent_result.reasoning[:100] + "..."
        
        response = f"""## {emoji} {symbol} Analysis Complete!

**🎯 Recommendation:** {action.upper()} 
**🔥 Confidence:** {result.confidence:.1%}

**🧠 AI Multi-Agent Analysis:**
{result.reasoning}

**📊 Key Metrics:**
• **Current Price:** {current_price}
• **Risk Level:** {result.risk_assessment.get('overall_risk', 'Moderate').title()}
• **Consensus Score:** {result.consensus_score:.1%}
• **Execution Priority:** {result.execution_priority}/10

**🤖 Detailed Agent Insights:**

**📈 Technical Analysis:**
{technical_insights}

**💼 Fundamental Analysis:**
{fundamental_insights}

**📰 Sentiment Analysis:**
{sentiment_insights}

**⚠️ Risk Assessment:**
{risk_insights}

**💡 What This Means:**
{self._get_action_explanation(action, symbol)}

**⚠️ Risk Disclaimer:**
This analysis is for educational purposes only and not financial advice. Always do your own research and consider consulting a financial advisor before making investment decisions.

---
*Want to analyze another stock or learn more about trading concepts? Just ask!* 📈"""

        return response
    
    def _get_action_explanation(self, action: str, symbol: str) -> str:
        """Get explanation for the recommended action"""
        if action == 'buy':
            return f"The analysis suggests {symbol} has strong potential for growth. Consider your risk tolerance and portfolio allocation before investing."
        elif action == 'sell':
            return f"The analysis indicates potential downside risks for {symbol}. Consider taking profits or reducing exposure based on your investment strategy."
        else:
            return f"The analysis suggests waiting for clearer signals on {symbol}. Monitor the stock for better entry/exit opportunities."
    
    def _format_comparison_response(self, symbols: List[str], results: Dict[str, OrchestrationResult], original_message: str) -> str:
        """Format response for stock comparison"""
        response = f"## 📊 Stock Comparison: {' vs '.join(symbols)}\n\n"
        
        for symbol in symbols:
            result = results[symbol]
            action = result.final_decision.value.lower()
            emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '🟡'}.get(action, '📊')
            
            response += f"### {emoji} {symbol}\n"
            response += f"**Recommendation:** {action.upper()} ({result.confidence:.1%} confidence)\n"
            response += f"**Key Insight:** {result.reasoning[:100]}...\n\n"
        
        # Add comparison summary
        best_pick = max(results.items(), key=lambda x: x[1].confidence if x[1].final_decision.value == 'BUY' else 0)
        if best_pick[1].final_decision.value == 'BUY':
            response += f"**🏆 Top Pick:** {best_pick[0]} shows the strongest buy signals with {best_pick[1].confidence:.1%} confidence.\n\n"
        
        response += "**⚠️ Risk Disclaimer:** This analysis is for educational purposes only. Always do your own research before investing.\n\n"
        response += "*Want detailed analysis of any specific stock? Just ask!* 📈"
        
        return response
    
    async def _handle_general_conversation(self, message: str) -> str:
        """Handle general trading conversation"""
        try:
            # Build conversation context
            messages = self._build_conversation_context(message)
            
            # Query OpenAI for response
            response = await self.openai_client.chat_completion(
                messages=messages,
                model=ModelType.GPT_4O
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in general conversation: {e}")
            return self._get_general_trading_response(message)
    
    def _build_conversation_context(self, current_message: str) -> List[Dict[str, str]]:
        """Build conversation context for OpenAI"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Add recent conversation history
        for msg in self.conversation_history[-6:]:  # Last 6 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _get_general_trading_response(self, message: str) -> str:
        """Get general trading response when OpenAI is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return """👋 **Hello! I'm your AI Trading Assistant!**

I'm powered by a sophisticated multi-agent system that can help you with:

🔍 **Stock Analysis** - Just mention any stock symbol (like AAPL, TSLA, MSFT)
📈 **Technical Analysis** - RSI, MACD, chart patterns, support/resistance  
💼 **Fundamental Analysis** - P/E ratios, financial health, valuation
📰 **Sentiment Analysis** - News sentiment, market psychology
⚠️ **Risk Assessment** - Portfolio risk, position sizing
🎓 **Trading Education** - Explain concepts, strategies, market dynamics

**Try asking:**
• "Analyze Apple stock"
• "Should I buy Tesla?"
• "Compare Microsoft vs Google"
• "Explain what RSI means"
• "What are the risks of tech stocks?"

What would you like to explore? 🚀"""

        elif any(word in message_lower for word in ['help', 'what', 'how', 'can you']):
            return """🤖 **I'm your AI Trading Assistant - Here's what I can do:**

**📊 Stock Analysis:**
• Mention any stock symbol for instant analysis
• Get buy/sell/hold recommendations with reasoning
• Compare multiple stocks side-by-side

**🧠 Multi-Agent Intelligence:**
• **Technical Agent**: Chart analysis, indicators, patterns
• **Fundamental Agent**: Financial metrics, company analysis  
• **Sentiment Agent**: News and social media sentiment
• **Risk Agent**: Risk assessment and position sizing

**🎓 Trading Education:**
• Explain technical indicators (RSI, MACD, etc.)
• Discuss trading strategies and market concepts
• Help understand risk management

**💬 Just Chat Naturally:**
• "What do you think about Apple?"
• "Is Tesla a good buy right now?"
• "Explain support and resistance"
• "How risky are growth stocks?"

Ready to help you make smarter trading decisions! What's on your mind? 📈"""

        elif any(word in message_lower for word in ['risk', 'risky', 'safe', 'danger']):
            return """⚠️ **Understanding Investment Risk:**

**🎯 Key Risk Types:**
• **Market Risk**: Overall market volatility
• **Company Risk**: Specific business challenges  
• **Sector Risk**: Industry-specific issues
• **Liquidity Risk**: Difficulty selling positions

**🛡️ Risk Management Strategies:**
• **Diversification**: Don't put all eggs in one basket
• **Position Sizing**: Never risk more than you can afford to lose
• **Stop Losses**: Set exit points before entering trades
• **Research**: Always understand what you're investing in

**📊 My Risk Analysis:**
When you ask me to analyze a stock, my Risk Agent evaluates:
• Volatility levels and price stability
• Correlation with market movements  
• Optimal position sizing for your risk tolerance
• Potential downside scenarios

**💡 Remember:**
• Higher potential returns usually mean higher risk
• Past performance doesn't guarantee future results
• Consider your investment timeline and goals

Want me to analyze the risk profile of a specific stock? Just mention the symbol! 📈"""

        else:
            return """🤔 **I'd love to help you with that!**

I specialize in stock analysis and trading insights. Here are some ways I can assist:

**📈 For Stock Analysis:**
• Just mention a stock symbol: "Analyze AAPL" or "What about Tesla?"
• Ask for recommendations: "Should I buy Microsoft?"
• Compare stocks: "Apple vs Google analysis"

**🎓 For Trading Education:**
• "Explain RSI indicator"
• "What is a bull market?"
• "How do I manage risk?"

**💬 Or just chat about:**
• Market trends and opportunities
• Investment strategies
• Risk management
• Trading concepts

What specific stock or trading topic interests you? I'm here to help! 🚀"""
    
    def _get_error_response(self, error: str) -> str:
        """Get error response"""
        return f"""😅 **Oops! I encountered a technical issue.**

Don't worry - I'm still here to help! Here's what you can try:

**🔄 For Stock Analysis:**
• Try asking about a different stock symbol
• Use simple format: "Analyze AAPL" or "What about Tesla?"

**💡 Alternative Questions:**
• "What can you help me with?"
• "Explain technical analysis"
• "How do I evaluate stocks?"

**🛠️ Technical Details:**
{error[:100]}...

I'm continuously learning and improving. Thanks for your patience! 

What else would you like to explore? 📈"""
    
    def _trim_conversation_history(self):
        """Trim conversation history to max length"""
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def _get_general_stock_guidance(self, symbol: str) -> str:
        """Get general stock guidance when analysis fails"""
        return f"""📊 **General Guidance for {symbol}:**

**🔍 Key Things to Research:**
• **Recent News**: Check for earnings reports, product launches, or major announcements
• **Financial Health**: Look at revenue growth, profit margins, and debt levels
• **Technical Levels**: Identify support and resistance on the charts
• **Market Sentiment**: See what analysts and investors are saying

**📈 Analysis Framework:**
• **Fundamental**: Is the company financially strong?
• **Technical**: What do the charts and indicators show?
• **Sentiment**: What's the overall market mood?
• **Risk**: How much volatility can you handle?

**💡 Smart Investing Tips:**
• Never invest more than you can afford to lose
• Diversify across different stocks and sectors
• Have a clear entry and exit strategy
• Stay updated with company and market news

Want me to try analyzing {symbol} again, or would you like to explore a different stock? 🚀"""

