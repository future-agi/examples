#!/bin/bash

echo "🚀 Setting up the 10-Agent System Demo"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Please create a .env file with your API keys."
    echo "Copy env_template.txt to .env and fill in your keys:"
    echo ""
    echo "  cp env_template.txt .env"
    echo ""
    echo "You need:"
    echo "  - OPENAI_API_KEY (required)"
    echo "  - TAVILY_API_KEY (required for web search)"
    echo "  - FI_API_KEY & FI_SECRET_KEY (optional for monitoring)"
    echo ""
    exit 1
fi

echo ""
echo "🎬 Running the Multi-Agent System..."
echo ""
python agent_system.py
