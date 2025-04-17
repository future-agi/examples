#!/usr/bin/env python3

import os
import sys
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
import argparse
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, EvalTag, EvalName, EvalTagType, EvalSpanKind
from opentelemetry import trace

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="ecom_agent",
    session_name="ecom_agent_observe",
)

trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ecommerce_agent.prototype")

# Import the main module and integrated agent
try:
    from app_main import IntegratedEcommerceAgent
except ImportError:
    # Fallback to main if app_main doesn't exist
    from main import EcommerceAgent as IntegratedEcommerceAgent

class EcommerceAgentPrototype:
    """
    Prototype for testing the e-commerce agent without a UI
    Simulates the user sending messages as they would through the Gradio interface
    """
    
    def __init__(self, debug=False):
        """Initialize the prototype with the agent"""
        self.debug = debug
        self.agent = IntegratedEcommerceAgent()
        self.conversation_history = []
        logger.info("E-commerce Agent Prototype initialized")
        
    def simulate_message(self, message: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate a user sending a message to the chatbot
        
        Args:
            message: The user's message
            image_path: Optional path to an image file
            
        Returns:
            Dict containing the agent's response and any additional data
        """
        logger.info(f"User message: {message}")
        if image_path:
            logger.info(f"With image: {image_path}")
            
        # Ensure image path exists if provided
        if image_path and not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {"error": f"Image file not found: {image_path}"}
            
        try:
            # Call the agent's process_query method - this is what would happen from the UI
            response, img_path = self.agent.process_query(message, image_path)
            
            # Store the conversation for later reference
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            result = {
                "response": response,
                "image_path": img_path
            }
            
            # Print the response for easy viewing in console
            print("\n" + "="*50)
            print(f"User: {message}")
            print(f"Agent: {response}")
            if img_path:
                print(f"Image generated: {img_path}")
            print("="*50 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if self.debug:
                import traceback
                logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def run_test_scenario(self, scenario_name: str = "basic"):
        """
        Run a predefined test scenario
        
        Args:
            scenario_name: Name of the scenario to run
        """
        scenarios = {
            "basic": [
                "Bluetooth Headphones .",
                "Show me the products under $50.",
                "I want to order the Bluetooth Headphones.",
                "Yes, please place the order."
            ],
            "image_recommendation": [
                {"message": "Can you recommend a product based on this image?", "image": "test_images/living_room.jpg"},
                "Show me more details about the first recommendation."
            ],
            "order_flow": [
                "I need a new smartphone stand",
                "How much is the adjustable stand?",
                "I'd like to order it please",
                "Yes, confirm my order",
                "What's the status of my order?"
            ],
            "cancel_order": [
                "I'd like to cancel my recent order",
                "Yes, I'm sure I want to cancel"
            ]
        }
        
        if scenario_name not in scenarios:
            logger.error(f"Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {', '.join(scenarios.keys())}")
            return
        
        print(f"\nRunning scenario: {scenario_name}\n")
        
        for step in scenarios[scenario_name]:
            if isinstance(step, str):
                self.simulate_message(step)
            elif isinstance(step, dict):
                self.simulate_message(step["message"], step.get("image"))
            
            # Add a small delay between messages for better readability
            import time
            time.sleep(1)
    
    def interactive_mode(self):
        """Run in interactive mode where the user can type messages directly"""
        print("\nE-commerce Agent Interactive Mode")
        print("Type your messages below. Type 'quit', 'exit', or 'q' to exit.")
        print("Type 'image:path_to_image' before your message to include an image.\n")
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Exiting interactive mode.")
                break
            
            # Check for image in input
            image_path = None
            if user_input.startswith('image:'):
                parts = user_input.split(' ', 1)
                image_path = parts[0][6:]  # Remove 'image:' prefix
                user_input = parts[1] if len(parts) > 1 else ""
            
            # Process the message
            self.simulate_message(user_input, image_path)


def main():
    """Main function to run the prototype"""
    parser = argparse.ArgumentParser(description='E-commerce Agent Prototype')
    parser.add_argument('--scenario', type=str, default=None, 
                        help='Run a predefined test scenario')
    parser.add_argument('--interactive', action='store_true', 
                        help='Run in interactive mode')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug mode')
    parser.add_argument('--message', type=str, default=None, 
                        help='Single message to process')
    parser.add_argument('--image', type=str, default=None, 
                        help='Path to image file to include with message')
    
    args = parser.parse_args()
    
    # Create prototype agent
    prototype = EcommerceAgentPrototype(debug=args.debug)
    
    # Create test_images directory if it doesn't exist
    os.makedirs("test_images", exist_ok=True)
    
    # Determine mode of operation
    if args.scenario:
        prototype.run_test_scenario(args.scenario)
    elif args.message:
        prototype.simulate_message(args.message, args.image)
    elif args.interactive:
        prototype.interactive_mode()
    else:
        # Default to interactive mode if no arguments are provided
        print("No arguments provided, running in interactive mode.")
        prototype.interactive_mode()


if __name__ == "__main__":
    main()
