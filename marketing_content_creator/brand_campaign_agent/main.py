#!/usr/bin/env python3
"""
Main entry point for the Brand Campaign Agent
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import app

if __name__ == "__main__":
    app()

