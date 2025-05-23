"""
Interview Agent - Main Application Entry Point
"""

import os
import sys

# Ensure the src directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



# Import the app from app.py
from app import app

# Launch the application
if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key before running the application:")
        print("export OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Launch the Gradio app
    app.launch(share=True)
