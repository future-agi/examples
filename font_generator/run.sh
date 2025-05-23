#!/bin/bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install openai gradio pillow requests

# Run the application
python app.py
