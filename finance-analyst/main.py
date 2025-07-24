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
import json
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from fi.evals import Protect 
from load_dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

import gradio as gr
import yfinance as yf
import re
from integrations.market_data.data_provider import market_data_manager
import requests
import pandas as pd

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType, SpanAttributes, FiSpanKindValues
from traceai_openai import OpenAIInstrumentor

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="finance_analyst",
    set_global_tracer_provider=True
)

OpenAIInstrumentor().instrument(tracer_provider=trace_provider)

tracer = FITracer(trace_provider.get_tracer(__name__))

# Function calling schemas for LLM routing
FUNCTION_SCHEMAS = [
    {
        "name": "analyze_stocks",
        "description": "Perform real-time stock analysis on up to 3 ticker symbols.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock tickers (max 3)"
                },
                "original_query": {
                    "type": "string",
                    "description": "Original user query"
                }
            },
            "required": ["symbols", "original_query"]
        }
    },
    {
        "name": "explain_concept",
        "description": "Provide an educational explanation of a trading or finance concept.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Concept to explain (e.g., RSI, P/E ratio)"
                }
            },
            "required": ["topic"]
        }
    }
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting for Yahoo Finance
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 1.0  # 1 second between requests

class AITradingAssistant:
    """
    AI Trading Assistant - Production Version
    Provides real-time stock analysis with live market data and AI-powered insights
    """
    
    def __init__(self):
        """Initialize the AI trading assistant"""
        logger.info("Initializing AI Trading Assistant...")
        
        # Simple cache for stock data
        self.stock_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        # Chat history management
        self.chat_history = []

        self.protector = Protect()
        self.protect_rules = [
        {
            'metric': 'content_moderation',
        },
        {
            'metric': 'data_privacy_compliance',
        },
        {
            'metric': 'bias_detection',
        },
        {
            'metric': 'security',
        }
                            ]
        self.action = "I am Sorry I can't assist with that query"
        self.use_flash = False
        
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
        with tracer.start_as_current_span("AITradingAssistant.process_message",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value,
                SpanAttributes.INPUT_VALUE: json.dumps(message),
            }) as span:

            """Route the user message using LLM function calling when available."""
            try:
                # Input protection - check user input first
                protection_result = self.protector.protect(inputs=message, protect_rules=self.protect_rules, action=self.action, use_flash=self.use_flash, reason=True)
                print(protection_result)    

                if protection_result.get("status") == "failed":
                    error_msg = protection_result.get("messages", "I cannot process this request")
                    logger.warning(f"Input protection failed: {protection_result.get('reason', 'Unknown reason')}")
                    # Add to history and return immediately - skip all processing
                    self.chat_history.append({"role": "user", "content": message})
                    self.chat_history.append({"role": "assistant", "content": error_msg})
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(error_msg))
                    return error_msg
                
                # Add user message to history
                self.chat_history.append({"role": "user", "content": message})
                
                # If OpenAI client exists, let the model decide what to do
                if self.openai_client:
                    router_sys_prompt = (
                        "You are a router for an AI trading assistant. "
                        "If the user wants stock analysis, call the analyze_stocks function. "
                        "If the user asks a conceptual question (education), call explain_concept. "
                        "Otherwise, answer normally."
                    )

                    # Build messages with history for context
                    context_messages = [
                        {"role": "system", "content": router_sys_prompt},
                        *self.chat_history[-10:]  # Keep last 10 messages for context
                    ]

                    response = await self.openai_client.chat_completion(
                        messages=context_messages,
                        model=self.model_type,
                        functions=FUNCTION_SCHEMAS,
                        function_call="auto"
                    )

                    choice = response.choices[0]
                    if choice.finish_reason == "function_call":
                        fn = choice.message.function_call
                        args = json.loads(fn.arguments or "{}")

                        if fn.name == "analyze_stocks":
                            result = await self._analyze_stocks(args.get("symbols", []), args.get("original_query", message))
                        elif fn.name == "explain_concept":
                            topic = args.get("topic", message)
                            result = await self._handle_general_query(topic)
                        
                        # Add assistant response to history
                        self.chat_history.append({"role": "assistant", "content": result})
                        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                        
                        # Final output protection
                        protected_result = self.protector.protect(inputs=result, protect_rules=self.protect_rules, action=self.action, use_flash=self.use_flash, reason=True)
                        print(protected_result)
                        if protected_result.get("status") == "failed":
                            result = "I am Sorry I can't assist with that query"
                            self.chat_history[-1] = {"role": "assistant", "content": result}  # Update last message
                        
                        return result
                        
                    # If no function_call, return the assistant content directly
                    result = choice.message.content
                    self.chat_history.append({"role": "assistant", "content": result})
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    
                    # Final output protection
                    protected_result = self.protector.protect(inputs=result, protect_rules=self.protect_rules, action=self.action, use_flash=self.use_flash, reason=True)
                    print(protected_result)
                    if protected_result.get("status") == "failed":
                        result = "I am Sorry I can't assist with that query"
                        self.chat_history[-1] = {"role": "assistant", "content": result}  # Update last message
                    
                    return result

                # Fallback path (no OpenAI client)
                stock_symbols = self._extract_stock_symbols(message)
                if stock_symbols:
                    result = await self._analyze_stocks(stock_symbols, message)
                else:
                    result = await self._handle_general_query(message)
                
                # Add assistant response to history
                self.chat_history.append({"role": "assistant", "content": result})
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                
                # Final output protection
                protected_result = self.protector.protect(inputs=result, protect_rules=self.protect_rules, action=self.action, use_flash=self.use_flash, reason=True)
                print(protected_result) 
                if protected_result.get("status") == "failed":
                    result = "I am Sorry I can't assist with that query"
                    self.chat_history[-1] = {"role": "assistant", "content": result}  # Update last message
                
                return result

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_msg = f"I encountered an error while processing your request: {str(e)}"
                self.chat_history.append({"role": "assistant", "content": error_msg})
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(error_msg))
                return error_msg
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the current chat history"""
        return self.chat_history.copy()
    
    def clear_chat_history(self):
        """Clear the chat history"""
        self.chat_history = []
        logger.info("Chat history cleared")
    
    def get_conversation_context(self, last_n: int = 5) -> str:
        with tracer.start_as_current_span("AITradingAssistant.get_conversation_context",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(last_n),
            }) as span:

            """Get conversation context as a formatted string"""
            if not self.chat_history:
                context_str = "No previous conversation."
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(context_str))
                return context_str
            
            context_messages = self.chat_history[-last_n * 2:]  # Get last n exchanges
            context_str = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content'][:100]}..."
                for msg in context_messages
            ])
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(context_str))
            return context_str
    
    async def _analyze_stocks(self, symbols: List[str], original_query: str) -> str:
        with tracer.start_as_current_span("AITradingAssistant.analyze_stocks",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value,
                SpanAttributes.INPUT_VALUE: json.dumps({"symbols": symbols, "original_query": original_query}),
            }) as span:

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
                    result = analyses[0]
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                elif len(analyses) > 1:
                    result = self._combine_analyses(analyses, original_query)
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                else:
                    result = "I couldn't retrieve data for the requested stocks. Please check the symbols and try again."
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                    
            except Exception as e:
                logger.error(f"Error in stock analysis: {e}")
                result = f"I encountered an error analyzing the stocks: {str(e)}"
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
    
    async def _get_real_stock_data(self, symbol: str) -> Optional[Dict]:
        with tracer.start_as_current_span("AITradingAssistant.get_real_stock_data",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(symbol),
            }) as span:

            """Get real stock data using yfinance with rate limiting and retry logic"""
            global LAST_REQUEST_TIME
            
            # Check cache first
            current_time = time.time()
            if symbol in self.stock_cache:
                cached_data, timestamp = self.stock_cache[symbol]
                if current_time - timestamp < self.cache_timeout:
                    logger.info(f"Using cached data for {symbol}")
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(cached_data))
                    return cached_data
            
            max_retries = 3
            base_delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    # Rate limiting
                    current_time = time.time()
                    time_since_last = current_time - LAST_REQUEST_TIME
                    if time_since_last < MIN_REQUEST_INTERVAL:
                        sleep_time = MIN_REQUEST_INTERVAL - time_since_last + random.uniform(0.1, 0.5)
                        await asyncio.sleep(sleep_time)
                    
                    LAST_REQUEST_TIME = time.time()
                    
                    info = {}
                    try:
                        # Fetch from Alpha Vantage directly (daily adjusted, compact = 100 rows)
                        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
                        if not api_key:
                            logger.warning("ALPHA_VANTAGE_API_KEY not set; cannot fetch data")
                            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(None))
                            return None

                        av_url = (
                            f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={api_key}"
                        )
                        print(av_url)
                        av_resp = requests.get(av_url, timeout=10)
                        av_json = av_resp.json()
                        ts = av_json.get("Weekly Adjusted Time Series", {})

                        if not ts:
                            logger.warning(f"Alpha Vantage returned no data for {symbol}: {av_json.get('Note') or av_json.get('Error Message')}")
                            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(None))
                            return None

                        df_raw = pd.DataFrame.from_dict(ts, orient="index")

                        rename_map = {
                            "1. open": "Open",
                            "2. high": "High",
                            "3. low": "Low",
                            "4. close": "Close",
                            "5. adjusted close": "Adj Close",
                            "6. volume": "Volume"
                        }

                        data = df_raw.rename(columns=rename_map)

                        # Keep only columns we renamed (others like dividend amount removed)
                        data = data[[c for c in rename_map.values() if c in data.columns]]

                        # Convert to numeric types
                        data = data.apply(pd.to_numeric, errors="coerce")
                        data.index = pd.to_datetime(data.index)
                        data = data.sort_index()
                        hist = data.tail(120)  # About 6 months of trading days

                        if hist.empty:
                            logger.warning(f"No historical data for {symbol} from Alpha Vantage")
                            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(None))
                            return None
                    except Exception as hist_error:
                        if "429" in str(hist_error):
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt) + random.uniform(1, 3)
                                logger.warning(f"Rate limited for {symbol} history, retrying in {delay:.1f}s (attempt {attempt + 1})")
                                await asyncio.sleep(delay)
                                continue
                            else:
                                logger.error(f"Max retries exceeded for {symbol} history")
                                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(None))
                                return None
                        raise hist_error
                    
                    # Calculate metrics
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close else 0
                    
                    # Get company overview from Alpha Vantage
                    overview = {}
                    try:
                        overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
                        overview_resp = requests.get(overview_url, timeout=10)
                        overview = overview_resp.json()
                        if "Note" in overview or "Error Message" in overview:
                            logger.warning(f"Alpha Vantage overview API limit or error for {symbol}")
                            overview = {}
                    except Exception as overview_err:
                        logger.warning(f"Failed to fetch overview for {symbol}: {overview_err}")
                        overview = {}

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
                    
                    # Cache the successful result
                    result = {
                        "symbol": symbol,
                        "current_price": current_price,
                        "change": change,
                        "change_percent": change_pct,
                        "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns and not pd.isna(hist['Volume'].iloc[-1]) else None,
                        "market_cap": float(overview.get('MarketCapitalization', 0)) if overview.get('MarketCapitalization') not in [None, 'None'] else None,
                        "pe_ratio": float(overview.get('PERatio', 0)) if overview.get('PERatio') not in [None, 'None'] else None,
                        "forward_pe": float(overview.get('ForwardPE', 0)) if overview.get('ForwardPE') not in [None, 'None'] else None,
                        "pb_ratio": float(overview.get('PriceToBookRatio', 0)) if overview.get('PriceToBookRatio') not in [None, 'None'] else None,
                        "dividend_yield": float(overview.get('DividendYield', 0)) * 100 if overview.get('DividendYield') not in [None, 'None', '0'] else 0,
                        "beta": float(overview.get('Beta', 0)) if overview.get('Beta') not in [None, 'None'] else None,
                        "rsi": current_rsi,
                        "sma_20": sma_20,
                        "sma_50": sma_50,
                        "52_week_high": float(overview.get('52WeekHigh', 0)) if overview.get('52WeekHigh') not in [None, 'None'] else None,
                        "52_week_low": float(overview.get('52WeekLow', 0)) if overview.get('52WeekLow') not in [None, 'None'] else None,
                        "sector": overview.get('Sector', 'N/A'),
                        "industry": overview.get('Industry', 'N/A'),
                        "company_name": overview.get('Name', symbol),
                        "description": overview.get('Description', ''),
                        "eps": float(overview.get('EPS', 0)) if overview.get('EPS') not in [None, 'None'] else None,
                        "revenue_ttm": float(overview.get('RevenueTTM', 0)) if overview.get('RevenueTTM') not in [None, 'None'] else None,
                        "profit_margin": float(overview.get('ProfitMargin', 0)) if overview.get('ProfitMargin') not in [None, 'None'] else None
                    }
                    
                    # Store in cache
                    self.stock_cache[symbol] = (result, time.time())
                    
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                    
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"Rate limited for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Error getting stock data for {symbol}: {e}")
                        break
            
            # If yfinance fails entirely, attempt fallback to MarketDataManager
            try:
                context = await market_data_manager.get_market_context(symbol)
                if context and context.get("current_price"):
                    logger.info(f"Used MarketDataManager fallback for {symbol}")
                    result = {
                        "symbol": symbol,
                        "current_price": context.get("current_price"),
                        "change": None,
                        "change_percent": None,
                        "volume": context.get("volume_data", [{}])[-1].get("volume", 0) if context.get("volume_data") else 0,
                        "market_cap": None,
                        "pe_ratio": None,
                        "forward_pe": None,
                        "pb_ratio": None,
                        "dividend_yield": None,
                        "beta": None,
                        "rsi": context.get("market_indicators", {}).get("rsi"),
                        "sma_20": context.get("market_indicators", {}).get("sma_20"),
                        "sma_50": context.get("market_indicators", {}).get("sma_50"),
                        "52_week_high": None,
                        "52_week_low": None,
                        "sector": None,
                        "industry": None,
                        "company_name": symbol
                    }
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
            except Exception as fallback_err:
                logger.error(f"Fallback market data failed for {symbol}: {fallback_err}")
            
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(None))
            return None
    
    async def _perform_real_analysis(self, symbol: str, data: Dict, query: str) -> str:
        with tracer.start_as_current_span("AITradingAssistant.perform_real_analysis",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value,
                SpanAttributes.INPUT_VALUE: json.dumps({"symbol": symbol, "query": query}),
            }) as span:

            """Perform real analysis with actual data"""
            try:
                # Use AI analysis if available
                if self.openai_client:
                    result = await self._ai_analysis(symbol, data, query)
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                else:
                    result = self._rule_based_analysis(symbol, data)
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                    return result
                    
            except Exception as e:
                logger.error(f"Error in analysis for {symbol}: {e}")
                result = self._rule_based_analysis(symbol, data)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
    
    async def _ai_analysis(self, symbol: str, data: Dict, query: str) -> str:
        with tracer.start_as_current_span("AITradingAssistant.ai_analysis",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                SpanAttributes.INPUT_VALUE: json.dumps({"symbol": symbol, "query": query}),
            }) as span:
            """AI-powered analysis using OpenAI"""
            try:
                def fmt_num(val, fmt=".2f", default="N/A"):
                    return format(val, fmt) if isinstance(val, (int, float)) else default

                current_price = fmt_num(data.get("current_price"))
                change_pct = fmt_num(data.get("change_percent"), "+.2f")
                volume = f"{int(data.get('volume', 0)):,}"
                mcap = f"${int(data.get('market_cap')):,}" if data.get("market_cap") else "N/A"
                pe_ratio = fmt_num(data.get("pe_ratio"), ".1f")
                pb_ratio = fmt_num(data.get("pb_ratio"), ".2f")
                dividend_yield = fmt_num(data.get("dividend_yield"), ".2f")
                beta = fmt_num(data.get("beta"), ".2f")
                rsi_val = fmt_num(data.get("rsi"), ".1f")
                sma20 = fmt_num(data.get("sma_20"))
                sma50 = fmt_num(data.get("sma_50"))
                wk_low = fmt_num(data.get("52_week_low"))
                wk_high = fmt_num(data.get("52_week_high"))

                analysis_prompt = (
                    f"Analyze {symbol} stock based on the following real market data:\n\n"
                    f"Company: {data.get('company_name', 'N/A')}\n"
                    f"Current Price: ${current_price}\n"
                    f"Change: {change_pct}%\n"
                    f"Volume: {volume}\n"
                    f"Market Cap: {mcap}\n"
                    f"P/E Ratio: {pe_ratio}\n"
                    f"P/B Ratio: {pb_ratio}\n"
                    f"Dividend Yield: {dividend_yield}%\n"
                    f"Beta: {beta}\n"
                    f"RSI: {rsi_val}\n"
                    f"20-day SMA: ${sma20}\n"
                    f"50-day SMA: ${sma50}\n"
                    f"52-week Range: ${wk_low} - ${wk_high}\n"
                    f"Sector: {data.get('sector', 'N/A')}\n"
                    f"Industry: {data.get('industry', 'N/A')}\n\n"
                    f"User Query: {query}\n\n"
                    "Provide a comprehensive analysis including:\n"
                    "1. Technical analysis (RSI, moving averages, trend)\n"
                    "2. Fundamental analysis (valuation, financial health)\n"
                    "3. Clear BUY/SELL/HOLD recommendation with confidence level\n"
                    "4. Risk assessment\n"
                    "5. Key actionable insights\n\n"
                    "Format as a professional analysis report with clear sections."
                )
                
                span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps({"symbol": symbol, "query": query, "prompt": analysis_prompt}))

                messages = [
                    {"role": "system", "content": "You are an expert financial analyst. Provide detailed, actionable stock analysis based on real market data."},
                    {"role": "user", "content": analysis_prompt}
                ]
                
                response = await self.openai_client.chat_completion(messages, self.model_type)
                result = response.choices[0].message.content
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
                
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                result = self._rule_based_analysis(symbol, data)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
    
    def _rule_based_analysis(self, symbol: str, data: Dict) -> str:
        with tracer.start_as_current_span("AITradingAssistant.rule_based_analysis",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(symbol),
            }) as span:

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
            
            result = f"""
    ## 📊 {symbol} - Real-Time Analysis

    **Company:** {data.get('company_name', symbol)}
    **Current Price:** ${price:.2f} ({change_pct:+.2f}%)
    **Volume:** {volume:,}

    ### 🎯 Investment Recommendation
    **Recommendation:** {recommendation}
    **Confidence Level:** {confidence}%

    ### �� Technical Analysis
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
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result
    
    def _combine_analyses(self, analyses: List[str], query: str) -> str:
        with tracer.start_as_current_span("AITradingAssistant.combine_analyses",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps({"query": query}),
            }) as span:

            """Combine multiple stock analyses"""
            header = f"""
                # 📊 Multi-Stock Analysis
                **Query:** {query}
                **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                ---

                """
            result = header + "\n\n---\n\n".join(analyses)
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result
    
    async def _handle_general_query(self, message: str) -> str:
        with tracer.start_as_current_span("AITradingAssistant.handle_general_query",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(message),
            }) as span:

            """Handle general trading questions"""
            message_lower = message.lower()
            
            # Trading education responses
            if any(term in message_lower for term in ['rsi', 'relative strength']):
                result = """
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
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
            
            elif any(term in message_lower for term in ['p/e', 'price to earnings', 'pe ratio']):
                result = """
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
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
            
            else:
                result = """
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
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
    
    def _extract_stock_symbols(self, message: str) -> List[str]:
        with tracer.start_as_current_span("AITradingAssistant.extract_stock_symbols",
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(message),
            }) as span:

            """Extract stock symbols from message"""
            # Common stock symbols (2-5 uppercase letters)
            symbols = re.findall(r'\b([A-Z]{2,5})\b', message.upper())
            
            # Filter out common words that aren't stocks
            exclude_words = {
                'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'WHAT', 'WERE', 'THEY', 'WE', 'BEEN', 'HAVE', 'THEIR', 'SAID', 'EACH', 'WHICH', 'SHE', 'DO', 'HOW', 'IF', 'WILL', 'UP', 'OTHER', 'ABOUT', 'OUT', 'MANY', 'THEN', 'THEM', 'THESE', 'SO', 'SOME', 'HER', 'WOULD', 'MAKE', 'LIKE', 'INTO', 'HIM', 'HAS', 'TWO', 'MORE', 'VERY', 'TO', 'OF', 'IN', 'IS', 'IT', 'WITH', 'AS', 'BE', 'ON', 'BY', 'THIS', 'THAT', 'FROM', 'OR', 'AN', 'AT', 'MY', 'YOUR', 'HIS', 'ME', 'US', 'WHO', 'WHEN', 'WHERE', 'WHY', 'STOCK', 'STOCKS', 'MARKET', 'PRICE', 'ANALYSIS', 'TRADING', 'INVEST', 'BUY', 'SELL', 'HOLD', 'HEY', 'HI', 'HELLO', 'PLEASE', 'TELL'
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
            
            result = filtered_symbols[:3]  # Limit to 3 symbols
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result


def create_gradio_interface():
    """Create Gradio interface for the AI Trading Assistant"""
    assistant = AITradingAssistant()
    
    def process_message(message, history):
        """Process message and return updated history"""
        if not message.strip():
            return history
        
        try:
            # Process message (reuse existing event loop if available)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(assistant.process_message(message))
            
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
    
    def clear_conversation():
        """Clear the conversation history"""
        assistant.clear_chat_history()
        return []  # Return empty history for Gradio
    
    # Modern dark theme CSS
    css = """
    body {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .gradio-container {
        max-width: 1000px !important;
        margin: 0 auto !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px;
        padding: 10px 0 20px 0;
    }
    .professional-header {
        background-color: #21262d;
        color: #f0f6fc;
        padding: 20px;
        border-radius: 8px;
        margin: 0 12px 20px 12px;
        text-align: center;
        border: 1px solid #30363d;
    }
    .chatbot {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 8px !important;
        height: 550px !important;
        overflow-y: auto !important;
    }
    .chatbot .message {
        max-width: 600px !important;
    }
 
    .message-row.bubble,
    .message-row.bubble > div {
        border: none !important;
        box-shadow: none !important;
        background-image: none !important;
    }
    .message-row.bubble::before,
    .message-row.bubble::after {
        display: none !important;
        content: none !important;
    }
 
    .chatbot ul {
        margin-left: 18px;
    }
    .message.user {
        background-color: #238636 !important;
        color: #fff !important;
    }
    .message.bot {
        background-color: #30363d !important;
        color: #c9d1d9 !important;
    }
    .sidebar-box {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 18px;
    }
    .gr-button.primary {
        background-color: #238636 !important;
        border-color: #2ea043 !important;
        color: #fff !important;
    }
    .gr-button.primary:hover {
        background-color: #2ea043 !important;
    }
    .gr-text-input input {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
    }
    .chatbot .message > div:first-child::before{
        display:none !important;
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
                    height=550,
                    show_label=False,
                    avatar_images=("👤", "🤖"),
                    type="messages",
                    elem_classes=["chatbot"]
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask me to analyze any stock (e.g., 'Analyze AAPL') or trading questions...",
                        container=False,
                        scale=4,
                        show_label=False
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Conversation", variant="secondary", scale=1)
            
            # Sidebar
            with gr.Column(scale=1):
                gr.HTML("""
                <div class="sidebar-box" style="text-align:center;">
                    <h3>🎯 Real Analysis Features</h3>
                </div>
                """)

                gr.HTML("""
                <div class="sidebar-box">
                    <h4>📊 Live Market Data</h4>
                    <ul>
                        <li>Real-time stock prices</li>
                        <li>Technical indicators (RSI, SMA)</li>
                        <li>Fundamental metrics (P/E, Market Cap)</li>
                        <li>Volume &amp; volatility data</li>
                    </ul>
                </div>
                """)

                gr.HTML("""
                <div class="sidebar-box">
                    <h4>🧠 Smart Analysis</h4>
                    <ul>
                        <li>AI-powered insights (when available)</li>
                        <li>Rule-based analysis fallback</li>
                        <li>BUY/SELL/HOLD recommendations</li>
                        <li>Confidence levels &amp; reasoning</li>
                    </ul>
                </div>
                """)

                gr.HTML("""
                <div class="sidebar-box">
                    <h4>💡 Try These Queries:</h4>
                    <ul style="font-size:0.9em;">
                        <li>Analyze AAPL</li>
                        <li>Compare AAPL vs MSFT</li>
                        <li>What is RSI?</li>
                        <li>Explain P/E ratio</li>
                        <li>Analyze TSLA stock</li>
                    </ul>
                </div>
                """)
        
        # Event handlers
        msg.submit(process_message, [msg, chatbot], [chatbot]).then(
            lambda: "", None, [msg]
        )
        submit_btn.click(process_message, [msg, chatbot], [chatbot]).then(
            lambda: "", None, [msg]
        )
        clear_btn.click(clear_conversation, [], [chatbot])
    
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
            server_port=7861,
            server_name="0.0.0.0",
            show_error=True
        )
    except Exception as e:
        print(f"❌ Error launching interface: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()

