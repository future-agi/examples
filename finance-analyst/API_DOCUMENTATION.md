# 🔧 API Documentation - AI Trading Assistant

**Technical documentation for developers and advanced users**

## 📋 Overview

The AI Trading Assistant is built with a modular architecture that allows for easy extension and customization. This document provides technical details about the system's components, APIs, and integration points.

## 🏗️ System Architecture

### Core Components

```
ai-trading-assistant-final/
├── main.py                 # Main application entry point
├── src/                    # Core system modules
│   ├── agents/            # Multi-agent system components
│   ├── integrations/      # External service integrations
│   ├── models/           # Data models and schemas
│   ├── orchestration/    # Agent coordination logic
│   ├── utils/            # Utility functions
│   └── knowledge/        # Knowledge base system
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── docs/                 # Documentation files
```

### Class Hierarchy

```python
AITradingAssistant
├── OpenAI Integration
├── Market Data Provider
├── Technical Analysis Engine
├── Fundamental Analysis Engine
└── Risk Assessment Module
```

## 🔌 Core APIs

### AITradingAssistant Class

**Main class that orchestrates all trading analysis functionality.**

```python
class AITradingAssistant:
    """
    AI Trading Assistant - Production Version
    Provides real-time stock analysis with live market data and AI-powered insights
    """
    
    def __init__(self):
        """Initialize the AI trading assistant"""
        
    async def process_message(self, message: str) -> str:
        """
        Process user message with real analysis
        
        Args:
            message (str): User input message
            
        Returns:
            str: Formatted analysis response
        """
```

### Stock Data Retrieval

```python
async def _get_real_stock_data(self, symbol: str) -> Optional[Dict]:
    """
    Get real stock data using yfinance
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        
    Returns:
        Optional[Dict]: Stock data dictionary or None if failed
        
    Data Structure:
    {
        "symbol": str,
        "current_price": float,
        "change": float,
        "change_percent": float,
        "volume": int,
        "market_cap": int,
        "pe_ratio": float,
        "forward_pe": float,
        "pb_ratio": float,
        "dividend_yield": float,
        "beta": float,
        "rsi": float,
        "sma_20": float,
        "sma_50": float,
        "52_week_high": float,
        "52_week_low": float,
        "sector": str,
        "industry": str,
        "company_name": str
    }
    """
```

### Analysis Methods

```python
async def _perform_real_analysis(self, symbol: str, data: Dict, query: str) -> str:
    """
    Perform real analysis with actual data
    
    Args:
        symbol (str): Stock symbol
        data (Dict): Stock data from _get_real_stock_data
        query (str): Original user query
        
    Returns:
        str: Formatted analysis report
    """

async def _ai_analysis(self, symbol: str, data: Dict, query: str) -> str:
    """
    AI-powered analysis using OpenAI
    
    Args:
        symbol (str): Stock symbol
        data (Dict): Stock data
        query (str): User query
        
    Returns:
        str: AI-generated analysis
    """

def _rule_based_analysis(self, symbol: str, data: Dict) -> str:
    """
    Rule-based analysis when AI is not available
    
    Args:
        symbol (str): Stock symbol
        data (Dict): Stock data
        
    Returns:
        str: Rule-based analysis report
    """
```

## 📊 Data Models

### Stock Data Schema

```python
from typing import Optional, Dict, Any

class StockData:
    """Stock data model"""
    
    symbol: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield: float
    beta: Optional[float]
    rsi: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    company_name: str
```

### Analysis Response Schema

```python
class AnalysisResponse:
    """Analysis response model"""
    
    symbol: str
    recommendation: str  # "BUY", "SELL", "HOLD"
    confidence: int      # 0-100
    current_price: float
    change_percent: float
    technical_analysis: Dict[str, Any]
    fundamental_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    reasoning: List[str]
    timestamp: str
```

## 🔗 Integration Points

### OpenAI Integration

```python
# src/integrations/openai/client.py

class OpenAIClient:
    """OpenAI API client for AI-powered analysis"""
    
    def __init__(self):
        """Initialize OpenAI client with API key from environment"""
        
    async def chat_completion(self, messages: List[Dict], model_type: ModelType) -> Any:
        """
        Send chat completion request to OpenAI
        
        Args:
            messages (List[Dict]): Chat messages
            model_type (ModelType): Model to use
            
        Returns:
            OpenAI response object
        """
```

### Market Data Integration

```python
# Market data provider using yfinance

import yfinance as yf

def get_stock_info(symbol: str) -> Dict:
    """
    Get comprehensive stock information
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        Dict: Stock information
    """
    ticker = yf.Ticker(symbol)
    return ticker.info

def get_historical_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Get historical price data
    
    Args:
        symbol (str): Stock symbol
        period (str): Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        
    Returns:
        pd.DataFrame: Historical price data
    """
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)
```

## 🧮 Technical Indicators

### RSI Calculation

```python
def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index
    
    Args:
        prices (pd.Series): Price series
        window (int): RSI period (default: 14)
        
    Returns:
        pd.Series: RSI values
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

### Moving Averages

```python
def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate Simple Moving Average
    
    Args:
        prices (pd.Series): Price series
        window (int): Moving average period
        
    Returns:
        pd.Series: SMA values
    """
    return prices.rolling(window=window).mean()

def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        prices (pd.Series): Price series
        window (int): EMA period
        
    Returns:
        pd.Series: EMA values
    """
    return prices.ewm(span=window).mean()
```

## 🎯 Analysis Logic

### Recommendation Engine

```python
def generate_recommendation(data: Dict) -> Tuple[str, int, List[str]]:
    """
    Generate investment recommendation based on analysis
    
    Args:
        data (Dict): Stock data
        
    Returns:
        Tuple[str, int, List[str]]: (recommendation, confidence, reasoning)
    """
    recommendation = "HOLD"
    confidence = 50
    reasoning = []
    
    # RSI analysis
    rsi = data.get('rsi')
    if rsi:
        if rsi < 30:
            recommendation = "BUY"
            confidence = 75
            reasoning.append(f"RSI ({rsi:.1f}) indicates oversold condition")
        elif rsi > 70:
            recommendation = "SELL"
            confidence = 75
            reasoning.append(f"RSI ({rsi:.1f}) indicates overbought condition")
    
    # P/E analysis
    pe_ratio = data.get('pe_ratio')
    if pe_ratio:
        if pe_ratio < 15:
            if recommendation != "SELL":
                recommendation = "BUY"
            confidence = min(confidence + 15, 85)
            reasoning.append(f"P/E ratio ({pe_ratio:.1f}) suggests undervaluation")
        elif pe_ratio > 30:
            reasoning.append(f"P/E ratio ({pe_ratio:.1f}) suggests high valuation")
    
    return recommendation, confidence, reasoning
```

### Risk Assessment

```python
def assess_risk(data: Dict) -> Dict[str, Any]:
    """
    Assess investment risk based on stock data
    
    Args:
        data (Dict): Stock data
        
    Returns:
        Dict[str, Any]: Risk assessment
    """
    beta = data.get('beta', 1.0)
    price = data.get('current_price', 0)
    week_52_high = data.get('52_week_high', 0)
    week_52_low = data.get('52_week_low', 0)
    
    # Volatility assessment
    if beta > 1.5:
        volatility = "High"
    elif beta > 1.0:
        volatility = "Moderate"
    else:
        volatility = "Low"
    
    # Market position
    if week_52_high and week_52_low:
        position_ratio = (price - week_52_low) / (week_52_high - week_52_low)
        if position_ratio > 0.9:
            market_position = "Near 52-week high"
        elif position_ratio < 0.1:
            market_position = "Near 52-week low"
        else:
            market_position = "Mid-range"
    else:
        market_position = "Unknown"
    
    return {
        "volatility": volatility,
        "beta": beta,
        "market_position": market_position,
        "position_ratio": position_ratio if 'position_ratio' in locals() else None
    }
```

## 🌐 Web Interface API

### Gradio Interface

```python
def create_gradio_interface():
    """Create Gradio interface for the AI Trading Assistant"""
    
    assistant = AITradingAssistant()
    
    def process_message(message, history):
        """Process message and return updated history"""
        # Implementation details...
        
    with gr.Blocks(css=css, title="AI Trading Assistant") as interface:
        # Interface components...
        
    return interface
```

### Custom CSS Styling

```css
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
```

## 🔧 Configuration

### Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))

# Application Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
SERVER_PORT = int(os.getenv('SERVER_PORT', '7860'))
```

### Logging Configuration

```python
import logging

def setup_logging():
    """Setup application logging"""
    
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('trading_assistant.log') if DEBUG_MODE else logging.NullHandler()
        ]
    )
```

## 🧪 Testing

### Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock

class TestAITradingAssistant(unittest.TestCase):
    """Test cases for AI Trading Assistant"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.assistant = AITradingAssistant()
    
    @patch('yfinance.Ticker')
    def test_get_stock_data(self, mock_ticker):
        """Test stock data retrieval"""
        # Mock yfinance response
        mock_ticker.return_value.info = {
            'symbol': 'AAPL',
            'regularMarketPrice': 150.0,
            'marketCap': 2500000000000
        }
        
        # Test the method
        result = asyncio.run(self.assistant._get_real_stock_data('AAPL'))
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['current_price'], 150.0)
    
    def test_symbol_extraction(self):
        """Test stock symbol extraction from text"""
        test_cases = [
            ("Analyze AAPL stock", ["AAPL"]),
            ("Compare AAPL vs MSFT", ["AAPL", "MSFT"]),
            ("What about Apple?", []),  # Should not extract common words
        ]
        
        for text, expected in test_cases:
            result = self.assistant._extract_stock_symbols(text)
            self.assertEqual(result, expected)
```

### Integration Tests

```python
class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_analysis_flow(self):
        """Test complete analysis workflow"""
        assistant = AITradingAssistant()
        
        # Test with a known stock
        result = asyncio.run(assistant.process_message("Analyze AAPL"))
        
        # Verify response structure
        self.assertIn("AAPL", result)
        self.assertIn("Current Price:", result)
        self.assertIn("Recommendation:", result)
        self.assertIn("RSI:", result)
```

## 🚀 Deployment

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app/src
ENV GRADIO_SERVER_NAME=0.0.0.0

# Run application
CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  ai-trading-assistant:
    build: .
    ports:
      - "7860:7860"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📈 Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_stock_data(symbol: str, cache_duration: int = 300):
    """
    Cache stock data for specified duration
    
    Args:
        symbol (str): Stock symbol
        cache_duration (int): Cache duration in seconds
        
    Returns:
        Cached stock data
    """
    # Implementation with timestamp checking
    pass
```

### Async Optimization

```python
import asyncio
import aiohttp

async def fetch_multiple_stocks(symbols: List[str]) -> Dict[str, Dict]:
    """
    Fetch multiple stocks concurrently
    
    Args:
        symbols (List[str]): List of stock symbols
        
    Returns:
        Dict[str, Dict]: Stock data for each symbol
    """
    tasks = [_get_real_stock_data(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        symbol: result for symbol, result in zip(symbols, results)
        if not isinstance(result, Exception)
    }
```

## 🔒 Security Considerations

### API Key Protection

```python
import os
from cryptography.fernet import Fernet

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_key = f.encrypt(api_key.encode())
    return encrypted_key.decode()

def decrypt_api_key(encrypted_key: str, key: str) -> str:
    """Decrypt API key for use"""
    f = Fernet(key.encode())
    decrypted_key = f.decrypt(encrypted_key.encode())
    return decrypted_key.decode()
```

### Input Validation

```python
import re

def validate_stock_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format
    
    Args:
        symbol (str): Stock symbol to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic validation: 1-5 uppercase letters
    pattern = r'^[A-Z]{1,5}$'
    return bool(re.match(pattern, symbol))

def sanitize_user_input(user_input: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        user_input (str): Raw user input
        
    Returns:
        str: Sanitized input
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', user_input)
    return sanitized.strip()
```

## 📊 Monitoring & Analytics

### Performance Metrics

```python
import time
from functools import wraps

def measure_performance(func):
    """Decorator to measure function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@measure_performance
async def _get_real_stock_data(self, symbol: str):
    """Measured stock data retrieval"""
    # Implementation...
```

### Usage Analytics

```python
class UsageTracker:
    """Track system usage for analytics"""
    
    def __init__(self):
        self.query_count = 0
        self.symbol_requests = {}
        self.response_times = []
    
    def track_query(self, query: str, response_time: float):
        """Track a user query"""
        self.query_count += 1
        self.response_times.append(response_time)
        
        # Extract symbols and track popularity
        symbols = self._extract_symbols(query)
        for symbol in symbols:
            self.symbol_requests[symbol] = self.symbol_requests.get(symbol, 0) + 1
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_queries": self.query_count,
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "popular_symbols": sorted(self.symbol_requests.items(), key=lambda x: x[1], reverse=True)[:10]
        }
```

## 🔧 Extension Points

### Custom Analysis Modules

```python
class CustomAnalysisModule:
    """Base class for custom analysis modules"""
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        """
        Perform custom analysis
        
        Args:
            symbol (str): Stock symbol
            data (Dict): Stock data
            
        Returns:
            Dict: Analysis results
        """
        raise NotImplementedError
    
    def get_recommendation(self, analysis: Dict) -> Tuple[str, int]:
        """
        Generate recommendation from analysis
        
        Args:
            analysis (Dict): Analysis results
            
        Returns:
            Tuple[str, int]: (recommendation, confidence)
        """
        raise NotImplementedError
```

### Plugin System

```python
class PluginManager:
    """Manage analysis plugins"""
    
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, name: str, plugin: CustomAnalysisModule):
        """Register a new analysis plugin"""
        self.plugins[name] = plugin
    
    def run_plugin(self, name: str, symbol: str, data: Dict) -> Dict:
        """Run a specific plugin"""
        if name in self.plugins:
            return self.plugins[name].analyze(symbol, data)
        raise ValueError(f"Plugin {name} not found")
```

## 📚 Additional Resources

### Useful Libraries

```python
# Financial data and analysis
import yfinance as yf          # Yahoo Finance data
import pandas as pd            # Data manipulation
import numpy as np             # Numerical computing

# Web interface
import gradio as gr            # Web UI framework

# AI and ML
import openai                  # OpenAI API
from transformers import pipeline  # Hugging Face models

# Utilities
import asyncio                 # Async programming
import aiohttp                 # Async HTTP client
import logging                 # Logging
from dotenv import load_dotenv # Environment variables
```

### External APIs

**Yahoo Finance (via yfinance)**:
- Real-time stock data
- Historical prices
- Company information
- Financial metrics

**OpenAI API**:
- GPT-4o for analysis
- Natural language processing
- Intelligent insights generation

### Development Tools

```bash
# Code formatting
black main.py

# Type checking
mypy main.py

# Linting
flake8 main.py

# Testing
pytest tests/

# Documentation
sphinx-build -b html docs/ docs/_build/
```

---

This API documentation provides a comprehensive technical reference for developers working with or extending the AI Trading Assistant. For user-focused documentation, refer to the README.md and USER_MANUAL.md files.

