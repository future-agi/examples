#!/usr/bin/env python3
"""
AI Trading Assistant - Production Version
Real-time stock analysis with live market data and AI-powered insights
"""

import os
import sys
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

import gradio as gr
import yfinance as yf
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITradingAssistant:
    """
    AI Trading Assistant - Production Version
    Provides real-time stock analysis with live market data and AI-powered insights
    """
    
    def __init__(self):
        """Initialize the AI trading assistant"""
        logger.info("Initializing AI Trading Assistant...")
        
        # Initialize OpenAI client if available
        self.openai_client = None
        try:
            from integrations.openai.client import OpenAIClient, ModelType
            self.openai_client = OpenAIClient()
            self.model_type = ModelType.GPT_4O
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
        
        logger.info("🤖 AI Trading Assistant initialized successfully")
    
    async def process_message(self, message: str) -> str:
        """
        Process user message with real analysis
        """
        try:
            # Extract stock symbols
            stock_symbols = self._extract_stock_symbols(message)
            
            if stock_symbols:
                # Perform real stock analysis
                return await self._analyze_stocks(stock_symbols, message)
            else:
                # Handle general queries
                return await self._handle_general_query(message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def _analyze_stocks(self, symbols: List[str], original_query: str) -> str:
        """Analyze stocks with real data"""
        try:
            analyses = []
            
            for symbol in symbols[:3]:  # Limit to 3 stocks
                # Get real market data
                stock_data = await self._get_real_stock_data(symbol)
                
                if stock_data:
                    # Perform real analysis
                    analysis = await self._perform_real_analysis(symbol, stock_data, original_query)
                    analyses.append(analysis)
                else:
                    analyses.append(f"❌ Could not retrieve data for {symbol}")
            
            if len(analyses) == 1:
                return analyses[0]
            elif len(analyses) > 1:
                return self._combine_analyses(analyses, original_query)
            else:
                return "I couldn't retrieve data for the requested stocks. Please check the symbols and try again."
                
        except Exception as e:
            logger.error(f"Error in stock analysis: {e}")
            return f"I encountered an error analyzing the stocks: {str(e)}"
    
    async def _get_real_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get real stock data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            # Calculate technical indicators
            sma_20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else None
            sma_50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
            
            # RSI calculation
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else None
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "change": change,
                "change_percent": change_pct,
                "volume": hist['Volume'].iloc[-1],
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "pb_ratio": info.get('priceToBook'),
                "dividend_yield": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                "beta": info.get('beta'),
                "rsi": current_rsi,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "company_name": info.get('longName', symbol)
            }
            
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {e}")
            return None
    
    async def _perform_real_analysis(self, symbol: str, data: Dict, query: str) -> str:
        """Perform real analysis with actual data"""
        try:
            # Use AI analysis if available
            if self.openai_client:
                return await self._ai_analysis(symbol, data, query)
            else:
                return self._rule_based_analysis(symbol, data)
                
        except Exception as e:
            logger.error(f"Error in analysis for {symbol}: {e}")
            return self._rule_based_analysis(symbol, data)
    
    async def _ai_analysis(self, symbol: str, data: Dict, query: str) -> str:
        """AI-powered analysis using OpenAI"""
        try:
            analysis_prompt = f"""
            Analyze {symbol} stock based on the following real market data:
            
            Company: {data.get('company_name', 'N/A')}
            Current Price: ${data.get('current_price', 0):.2f}
            Change: {data.get('change_percent', 0):+.2f}%
            Volume: {data.get('volume', 0):,}
            Market Cap: ${data.get('market_cap', 0):,} if data.get('market_cap') else 'N/A'
            P/E Ratio: {data.get('pe_ratio', 'N/A')}
            P/B Ratio: {data.get('pb_ratio', 'N/A')}
            Dividend Yield: {data.get('dividend_yield', 0):.2f}%
            Beta: {data.get('beta', 'N/A')}
            RSI: {data.get('rsi', 'N/A'):.1f if data.get('rsi') else 'N/A'}
            20-day SMA: ${data.get('sma_20', 0):.2f if data.get('sma_20') else 'N/A'}
            50-day SMA: ${data.get('sma_50', 0):.2f if data.get('sma_50') else 'N/A'}
            52-week Range: ${data.get('52_week_low', 0):.2f} - ${data.get('52_week_high', 0):.2f}
            Sector: {data.get('sector', 'N/A')}
            Industry: {data.get('industry', 'N/A')}
            
            User Query: {query}
            
            Provide a comprehensive analysis including:
            1. Technical analysis (RSI, moving averages, trend)
            2. Fundamental analysis (valuation, financial health)
            3. Clear BUY/SELL/HOLD recommendation with confidence level
            4. Risk assessment
            5. Key actionable insights
            
            Format as a professional analysis report with clear sections.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert financial analyst. Provide detailed, actionable stock analysis based on real market data."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.openai_client.chat_completion(messages, self.model_type)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._rule_based_analysis(symbol, data)
    
    def _rule_based_analysis(self, symbol: str, data: Dict) -> str:
        """Rule-based analysis when AI is not available"""
        price = data.get('current_price', 0)
        change_pct = data.get('change_percent', 0)
        rsi = data.get('rsi')
        pe_ratio = data.get('pe_ratio')
        volume = data.get('volume', 0)
        market_cap = data.get('market_cap', 0)
        sma_20 = data.get('sma_20')
        sma_50 = data.get('sma_50')
        
        # Pre-format values to avoid f-string issues
        rsi_formatted = f"{rsi:.1f}" if rsi else "N/A"
        rsi_status = "Oversold" if rsi and rsi < 30 else "Overbought" if rsi and rsi > 70 else "Neutral" if rsi else "N/A"
        sma_20_formatted = f"${sma_20:.2f}" if sma_20 else "N/A"
        sma_50_formatted = f"${sma_50:.2f}" if sma_50 else "N/A"
        pe_formatted = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
        market_cap_formatted = f"${market_cap:,}" if market_cap else "N/A"
        
        # Generate recommendation based on rules
        recommendation = "HOLD"
        confidence = 50
        reasoning = []
        
        # RSI analysis
        if rsi:
            if rsi < 30:
                recommendation = "BUY"
                confidence = 75
                reasoning.append(f"RSI ({rsi:.1f}) indicates oversold condition")
            elif rsi > 70:
                recommendation = "SELL"
                confidence = 75
                reasoning.append(f"RSI ({rsi:.1f}) indicates overbought condition")
            else:
                reasoning.append(f"RSI ({rsi:.1f}) is in neutral range")
        
        # P/E analysis
        if pe_ratio:
            if pe_ratio < 15:
                if recommendation != "SELL":
                    recommendation = "BUY"
                confidence = min(confidence + 15, 85)
                reasoning.append(f"P/E ratio ({pe_ratio:.1f}) suggests undervaluation")
            elif pe_ratio > 30:
                reasoning.append(f"P/E ratio ({pe_ratio:.1f}) suggests high valuation")
            else:
                reasoning.append(f"P/E ratio ({pe_ratio:.1f}) is reasonable")
        
        # Price momentum
        if change_pct > 5:
            reasoning.append("Strong positive momentum")
        elif change_pct < -5:
            reasoning.append("Significant price decline")
        
        # Moving average analysis
        sma_20 = data.get('sma_20')
        sma_50 = data.get('sma_50')
        if sma_20 and sma_50:
            if price > sma_20 > sma_50:
                reasoning.append("Price above both 20-day and 50-day moving averages (bullish)")
            elif price < sma_20 < sma_50:
                reasoning.append("Price below both moving averages (bearish)")
        
        return f"""
## 📊 {symbol} - Real-Time Analysis

**Company:** {data.get('company_name', symbol)}
**Current Price:** ${price:.2f} ({change_pct:+.2f}%)
**Volume:** {volume:,}

### 🎯 Investment Recommendation
**Recommendation:** {recommendation}
**Confidence Level:** {confidence}%

### 📈 Technical Analysis
**RSI:** {rsi_formatted} - {rsi_status}
**20-day SMA:** {sma_20_formatted}
**50-day SMA:** {sma_50_formatted}
**Price Trend:** {'Bullish' if change_pct > 2 else 'Bearish' if change_pct < -2 else 'Neutral'}

### 💰 Fundamental Metrics
**Market Cap:** {market_cap_formatted}
**P/E Ratio:** {pe_formatted}
**P/B Ratio:** {data.get('pb_ratio', 'N/A')}
**Dividend Yield:** {data.get('dividend_yield', 0):.2f}%
**Beta:** {data.get('beta', 'N/A')}

### 🏢 Company Information
**Sector:** {data.get('sector', 'N/A')}
**Industry:** {data.get('industry', 'N/A')}
**52-Week Range:** ${data.get('52_week_low', 0):.2f} - ${data.get('52_week_high', 0):.2f}

### 🧠 Analysis Reasoning
{chr(10).join(f"• {reason}" for reason in reasoning)}

### ⚠️ Risk Assessment
**Volatility:** {'High' if data.get('beta', 1) > 1.5 else 'Moderate' if data.get('beta', 1) > 1 else 'Low'} (Beta: {data.get('beta', 'N/A')})
**Market Position:** {'Near 52-week high' if price > data.get('52_week_high', 0) * 0.9 else 'Near 52-week low' if price < data.get('52_week_low', float('inf')) * 1.1 else 'Mid-range'}

### 📝 Key Takeaways
• Current analysis based on real-time market data
• Consider your risk tolerance and investment timeline
• Monitor upcoming earnings and sector developments
• This is not financial advice - conduct your own research

*Analysis generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with live market data*
        """
    
    def _combine_analyses(self, analyses: List[str], query: str) -> str:
        """Combine multiple stock analyses"""
        header = f"""
# 📊 Multi-Stock Analysis
**Query:** {query}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        return header + "\n\n---\n\n".join(analyses)
    
    async def _handle_general_query(self, message: str) -> str:
        """Handle general trading questions"""
        message_lower = message.lower()
        
        # Trading education responses
        if any(term in message_lower for term in ['rsi', 'relative strength']):
            return """
## 📈 RSI (Relative Strength Index) Explained

**What is RSI?**
RSI is a momentum oscillator that measures the speed and change of price movements, ranging from 0 to 100.

**How to Use RSI:**
• **RSI < 30:** Potentially oversold (buy signal)
• **RSI > 70:** Potentially overbought (sell signal)
• **RSI 30-70:** Neutral zone

**Key Points:**
• Best used with other indicators
• Works well in ranging markets
• Can give false signals in strong trends
• 14-period is the standard setting

**Trading Strategy:**
1. Look for RSI divergence with price
2. Wait for RSI to exit extreme zones
3. Confirm with price action and volume
4. Set appropriate stop-losses
            """
        
        elif any(term in message_lower for term in ['p/e', 'price to earnings', 'pe ratio']):
            return """
## 💰 P/E Ratio (Price-to-Earnings) Explained

**What is P/E Ratio?**
P/E ratio compares a company's stock price to its earnings per share (EPS).

**Formula:** Stock Price ÷ Earnings Per Share

**Interpretation:**
• **Low P/E (< 15):** Potentially undervalued or slow growth
• **High P/E (> 25):** High growth expectations or overvalued
• **Industry comparison is crucial**

**Types:**
• **Trailing P/E:** Based on past 12 months earnings
• **Forward P/E:** Based on projected earnings

**Limitations:**
• Doesn't account for growth rates
• Can be misleading for cyclical companies
• Negative earnings make P/E meaningless
            """
        
        else:
            return """
## 🤖 AI Trading Assistant

I'm here to help you with stock analysis and trading education!

**What I can do:**
• Analyze individual stocks (e.g., "Analyze AAPL")
• Compare multiple stocks (e.g., "Compare AAPL vs MSFT")
• Explain trading concepts (e.g., "What is RSI?")
• Provide real-time market data and analysis

**Try asking:**
• "Analyze [STOCK SYMBOL]"
• "What is [TRADING CONCEPT]?"
• "Compare [STOCK1] vs [STOCK2]"
• "Explain P/E ratio"

**Note:** All analysis is based on real-time market data and is for educational purposes only. Always conduct your own research before making investment decisions.
            """
    
    def _extract_stock_symbols(self, message: str) -> List[str]:
        """Extract stock symbols from message"""
        # Common stock symbols (2-5 uppercase letters)
        symbols = re.findall(r'\b([A-Z]{2,5})\b', message.upper())
        
        # Filter out common words that aren't stocks
        exclude_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'WHAT', 'WERE', 'THEY', 'WE', 'BEEN', 'HAVE', 'THEIR', 'SAID', 'EACH', 'WHICH', 'SHE', 'DO', 'HOW', 'IF', 'WILL', 'UP', 'OTHER', 'ABOUT', 'OUT', 'MANY', 'THEN', 'THEM', 'THESE', 'SO', 'SOME', 'HER', 'WOULD', 'MAKE', 'LIKE', 'INTO', 'HIM', 'HAS', 'TWO', 'MORE', 'VERY', 'TO', 'OF', 'IN', 'IS', 'IT', 'WITH', 'AS', 'BE', 'ON', 'BY', 'THIS', 'THAT', 'FROM', 'OR', 'AN', 'AT', 'MY', 'YOUR', 'HIS', 'ME', 'US', 'WHO', 'WHEN', 'WHERE', 'WHY', 'STOCK', 'STOCKS', 'MARKET', 'PRICE', 'ANALYSIS', 'TRADING', 'INVEST', 'BUY', 'SELL', 'HOLD'
        }
        
        # Common ticker symbol corrections for frequent mistakes
        ticker_corrections = {
            'APPL': 'AAPL',    # Apple Inc. - common typo
            'GOOGL': 'GOOGL',  # Already correct
            'GOOG': 'GOOGL',   # Google Class A -> Class A (GOOGL)
            'MSFT': 'MSFT',    # Already correct
            'AMZN': 'AMZN',    # Already correct
            'TSLA': 'TSLA',    # Already correct
            'META': 'META',    # Already correct
            'NVDA': 'NVDA',    # Already correct
            'NFLX': 'NFLX',    # Already correct
        }
        
        # Known stock symbols to prioritize
        known_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'V', 'JPM', 'JNJ', 'WMT', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX', 'CMCSA', 'PEP', 'ABT', 'COST', 'TMO', 'AVGO', 'XOM', 'NKE', 'LLY', 'ABBV', 'ACN', 'DHR', 'VZ', 'TXN', 'QCOM', 'BMY', 'PM', 'HON', 'UNP', 'IBM', 'SBUX', 'LOW', 'AMD', 'INTC', 'CVX', 'ORCL', 'MDT', 'AMGN', 'NEE', 'PFE', 'T', 'MO', 'GE', 'CAT', 'BA', 'GS', 'MMM', 'AXP', 'WBA', 'CVS', 'KO', 'MCD', 'RTX'
        }
        
        # Apply ticker symbol corrections first
        corrected_symbols = []
        for symbol in symbols:
            if symbol in ticker_corrections:
                corrected_symbol = ticker_corrections[symbol]
                if symbol != corrected_symbol:
                    logger.info(f"Corrected ticker symbol: {symbol} -> {corrected_symbol}")
                corrected_symbols.append(corrected_symbol)
            else:
                corrected_symbols.append(symbol)
        
        # Filter symbols
        filtered_symbols = []
        for symbol in corrected_symbols:
            if symbol in known_stocks:
                filtered_symbols.append(symbol)
            elif symbol not in exclude_words and len(symbol) <= 5:
                # Additional validation for unknown symbols
                if not any(char.isdigit() for char in symbol):  # No numbers
                    filtered_symbols.append(symbol)
        
        return filtered_symbols[:3]  # Limit to 3 symbols


def create_gradio_interface():
    """Create Gradio interface for the AI Trading Assistant"""
    assistant = AITradingAssistant()
    
    def process_message(message, history):
        """Process message and return updated history"""
        if not message.strip():
            return history
        
        try:
            # Process message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(assistant.process_message(message))
            loop.close()
            
            # Update history
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            
            return history
            
        except Exception as e:
            logger.error(f"Error in Gradio interface: {e}")
            error_response = f"I apologize, but I encountered an error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_response})
            return history
    
    # Professional CSS
    css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
        background-color: #f8f9fa !important;
    }
    .chat-container {
        height: 600px !important;
        background-color: #ffffff !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
    }
    .professional-header {
        background-color: #212529;
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #343a40;
    }
    """
    
    with gr.Blocks(css=css, title="AI Trading Assistant") as interface:
        gr.HTML("""
        <div class="professional-header">
            <h1>🚀 AI Trading Assistant</h1>
            <p>Real-Time Stock Analysis • Live Market Data • AI-Powered Insights</p>
            <p>✨ Professional trading analysis with real market data ✨</p>
        </div>
        """)
        
        with gr.Row():
            # Main chat interface
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[],
                    height=650,
                    show_label=False,
                    avatar_images=("👤", "🤖"),
                    type="messages"
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask me to analyze any stock (e.g., 'Analyze AAPL') or trading questions...",
                        container=False,
                        scale=4,
                        show_label=False
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
            
            # Sidebar
            with gr.Column(scale=1):
                gr.HTML("""
                <div style="background-color: #495057; color: white; padding: 12px; border-radius: 6px; margin-bottom: 15px; text-align: center;">
                    <h3>🎯 Real Analysis Features</h3>
                </div>
                """)
                
                gr.HTML("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6;">
                    <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                        <h4>📊 Live Market Data</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Real-time stock prices</li>
                            <li>Technical indicators (RSI, SMA)</li>
                            <li>Fundamental metrics (P/E, Market Cap)</li>
                            <li>Volume and volatility data</li>
                        </ul>
                    </div>
                </div>
                """)
                
                gr.HTML("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6;">
                    <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                        <h4>🧠 Smart Analysis</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>AI-powered insights (when available)</li>
                            <li>Rule-based analysis fallback</li>
                            <li>BUY/SELL/HOLD recommendations</li>
                            <li>Confidence levels and reasoning</li>
                        </ul>
                    </div>
                </div>
                """)
                
                gr.HTML("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6;">
                    <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                        <h4>💡 Try These Queries:</h4>
                        <ul style="margin: 10px 0; padding-left: 20px; font-size: 0.9em;">
                            <li>"Analyze AAPL"</li>
                            <li>"Compare AAPL vs MSFT"</li>
                            <li>"What is RSI?"</li>
                            <li>"Explain P/E ratio"</li>
                            <li>"Analyze TSLA stock"</li>
                        </ul>
                    </div>
                </div>
                """)
        
        # Event handlers
        msg.submit(process_message, [msg, chatbot], [chatbot]).then(
            lambda: "", None, [msg]
        )
        submit_btn.click(process_message, [msg, chatbot], [chatbot]).then(
            lambda: "", None, [msg]
        )
    
    return interface


def main():
    """Main function to launch the AI Trading Assistant"""
    print("🚀 Starting AI Trading Assistant")
    print("=" * 60)
    print("✅ Real-time market data integration")
    print("✅ Live stock analysis with technical indicators")
    print("✅ AI-powered insights and recommendations")
    print("✅ Professional trading education")
    print("✅ Clean, responsive web interface")
    print("=" * 60)
    
    try:
        interface = create_gradio_interface()
        interface.launch(
            share=True,
            server_port=7860,
            server_name="0.0.0.0",
            show_error=True
        )
    except Exception as e:
        print(f"❌ Error launching interface: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()

