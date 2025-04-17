#!/usr/bin/env python3

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main application
from app_main import create_interface

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='E-commerce Agent with Gradio Interface')
    parser.add_argument('--port', type=int, default=7860, help='Port to run the Gradio interface on')
    parser.add_argument('--share', action='store_true', help='Create a shareable link')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set in .env file. Please set it before using image processing features.")
        print("You can still test other features without the API key.")
    
    # Create directories
    os.makedirs("rendered_products", exist_ok=True)
    
    # Create and launch the interface
    print(f"Starting E-commerce Agent on port {args.port}...")
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        debug=args.debug
    )
    print("E-commerce Agent is running!")

if __name__ == "__main__":
    main()
