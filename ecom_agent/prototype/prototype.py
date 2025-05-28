#!/usr/bin/env python3

import os
import sys
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import argparse
import time
from datetime import datetime

import dotenv
dotenv.load_dotenv()

from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, EvalTag, EvalName, EvalTagType, EvalSpanKind
from opentelemetry import trace

eval_tag = [
    EvalTag(
        eval_name=EvalName.TOXICITY,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={},
        mapping={
            "input": "raw.input"
        },
        custom_eval_name="Toxicity"
    ),
    EvalTag(
        eval_name=EvalName.TONE,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={},
        mapping={
            "input": "raw.input"
        },
        custom_eval_name="Tone"
    ),
    EvalTag(
        eval_name=EvalName.SEXIST,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={},
        mapping={
            "input": "raw.input"
        },
        custom_eval_name="Sexist"
    ),
    EvalTag(
        eval_name=EvalName.EVALUATE_LLM_FUNCTION_CALLING,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.TOOL,
        config={},
        mapping={
            "input": "raw.input",
            "output": "raw.output"
        },
        custom_eval_name="LLM Function Calling"
    ),
    EvalTag(
        eval_name=EvalName.CONVERSATION_RESOLUTION,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={},
        mapping={
            "output": "raw.output"
        },
        custom_eval_name="Conversation Resolution"
    ),
    EvalTag(
        eval_name=EvalName.EVAL_IMAGE_INSTRUCTION,
        type=EvalTagType.OBSERVATION_SPAN,
        value=EvalSpanKind.LLM,
        config={},
        mapping={
            "input": "raw.input",
            "image_url": "image.url"
        },
        custom_eval_name="Image Instruction"
    ),
]

trace_provider = register(
    project_type=ProjectType.EXPERIMENT,
    project_name="ecom_agent_experiment-1",
    project_version_name="v4",
    eval_tags=eval_tag
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

# Define conversation datasets
CONVERSATION_DATASETS = {
    "product_discovery": [
        {
            "id": "pd_1",
            "message": "Hi, I'm looking for a new laptop for work",
            "expected_skill": "chat",
            "description": "Initial greeting and general inquiry"
        },
        {
            "id": "pd_2", 
            "message": "I need something with at least 16GB RAM and good battery life",
            "expected_skill": "search",
            "description": "Specific product requirements"
        },
        {
            "id": "pd_3",
            "message": "Can you show me the top 3 options under $1500?",
            "expected_skill": "search",
            "description": "Price-filtered search with context"
        },
        {
            "id": "pd_4",
            "message": "Tell me more about the second option",
            "expected_skill": "chat",
            "description": "Reference to previous results"
        },
        {
            "id": "pd_5",
            "message": "Generate an image of how it would look on a minimalist desk setup",
            "expected_skill": "image_generation",
            "description": "Image generation with product context"
        }
    ],
    
    "shopping_journey": [
        {
            "id": "sj_1",
            "message": "Find me wireless headphones for running",
            "expected_skill": "search",
            "description": "Product search"
        },
        {
            "id": "sj_2",
            "message": "I prefer ones with noise cancellation under $200",
            "expected_skill": "search",
            "description": "Refined search with criteria"
        },
        {
            "id": "sj_3",
            "message": "Show me customer reviews for the Sony ones",
            "expected_skill": "chat",
            "description": "Review inquiry with context"
        },
        {
            "id": "sj_4",
            "message": "I'll take the Sony WH-1000XM4",
            "expected_skill": "order",
            "description": "Order initiation"
        },
        {
            "id": "sj_5",
            "message": "yes",
            "expected_skill": "order",
            "description": "Order confirmation"
        }
    ],
    
    "visual_shopping": [
        {
            "id": "vs_1",
            "message": "I need a new office chair",
            "expected_skill": "search",
            "description": "Initial product search"
        },
        {
            "id": "vs_2",
            "message": "Generate an image of an ergonomic office chair in black",
            "expected_skill": "image_generation",
            "description": "Image generation request"
        },
        {
            "id": "vs_3",
            "message": "Can you change the color to blue?",
            "expected_skill": "image_editing",
            "description": "Image editing with context"
        },
        {
            "id": "vs_4",
            "message": "Now show me real products that look similar",
            "expected_skill": "search",
            "description": "Search based on generated image"
        },
        {
            "id": "vs_5",
            "message": "What's the warranty on the Herman Miller chair?",
            "expected_skill": "chat",
            "description": "Product detail inquiry"
        }
    ],
    
    "order_management": [
        {
            "id": "om_1",
            "message": "Show me my recent orders",
            "expected_skill": "order",
            "description": "Order history request"
        },
        {
            "id": "om_2",
            "message": "What's the status of order 12345?",
            "expected_skill": "order",
            "description": "Specific order status"
        },
        {
            "id": "om_3",
            "message": "Can I cancel that order?",
            "expected_skill": "order",
            "description": "Order cancellation with context"
        },
        {
            "id": "om_4",
            "message": "Actually, nevermind. When will it arrive?",
            "expected_skill": "order",
            "description": "Delivery inquiry"
        },
        {
            "id": "om_5",
            "message": "Thanks for the help!",
            "expected_skill": "chat",
            "description": "Closing conversation"
        }
    ],
    
    "mixed_conversation": [
        {
            "id": "mc_1",
            "message": "Hello! I'm redecorating my home office",
            "expected_skill": "chat",
            "description": "Opening statement"
        },
        {
            "id": "mc_2",
            "message": "Generate an image of a modern home office with plants",
            "expected_skill": "image_generation",
            "description": "Visual inspiration"
        },
        {
            "id": "mc_3",
            "message": "I love it! Now find me a desk lamp that would match this style",
            "expected_skill": "search",
            "description": "Product search based on generated image"
        },
        {
            "id": "mc_4",
            "message": "What about desk organizers?",
            "expected_skill": "search",
            "description": "Related product search"
        },
        {
            "id": "mc_5",
            "message": "Order the bamboo desk organizer set",
            "expected_skill": "order",
            "description": "Order placement"
        },
        {
            "id": "mc_6",
            "message": "yes, confirm the order",
            "expected_skill": "order",
            "description": "Order confirmation"
        },
        {
            "id": "mc_7",
            "message": "Great! Can you also suggest some wall art?",
            "expected_skill": "search",
            "description": "Continue shopping after order"
        }
    ]
}

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
        self.test_results = []
        logger.info("E-commerce Agent Prototype initialized")
        
    def simulate_message(self, message: str, image_path: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Simulate a user sending a message to the chatbot
        
        Args:
            message: The user's message
            image_path: Optional path to an image file
            metadata: Optional metadata about the message (id, expected_skill, etc.)
            
        Returns:
            Dict containing the agent's response and any additional data
        """
        start_time = time.time()
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
            self.conversation_history.append({
                "role": "user", 
                "content": message,
                "metadata": metadata
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response,
                "image_path": img_path
            })
            
            elapsed_time = time.time() - start_time
            
            result = {
                "response": response,
                "image_path": img_path,
                "elapsed_time": elapsed_time,
                "metadata": metadata
            }
            
            # Store test result if metadata is provided
            if metadata:
                test_result = {
                    "id": metadata.get("id"),
                    "message": message,
                    "response": response,
                    "expected_skill": metadata.get("expected_skill"),
                    "success": True,
                    "elapsed_time": elapsed_time
                }
                self.test_results.append(test_result)
            
            # Print the response for easy viewing in console
            print("\n" + "="*50)
            if metadata:
                print(f"[{metadata.get('id')}] {metadata.get('description', '')}")
            print(f"User: {message}")
            print(f"Agent: {response[:200]}..." if len(response) > 200 else f"Agent: {response}")
            if img_path:
                print(f"Image generated: {img_path}")
            print(f"Response time: {elapsed_time:.2f}s")
            print("="*50 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if self.debug:
                import traceback
                logger.error(traceback.format_exc())
            
            # Store test failure
            if metadata:
                test_result = {
                    "id": metadata.get("id"),
                    "message": message,
                    "response": str(e),
                    "expected_skill": metadata.get("expected_skill"),
                    "success": False,
                    "error": str(e)
                }
                self.test_results.append(test_result)
            
            return {"error": str(e)}
    
    def run_conversation_dataset(self, dataset_name: str, delay: float = 1.0):
        """
        Run a conversation dataset maintaining context between messages
        
        Args:
            dataset_name: Name of the dataset to run
            delay: Delay between messages in seconds
        """
        if dataset_name not in CONVERSATION_DATASETS:
            logger.error(f"Unknown dataset: {dataset_name}")
            print(f"Available datasets: {', '.join(CONVERSATION_DATASETS.keys())}")
            return
        
        dataset = CONVERSATION_DATASETS[dataset_name]
        print(f"\n{'='*60}")
        print(f"Running Conversation Dataset: {dataset_name}")
        print(f"Total messages: {len(dataset)}")
        print(f"{'='*60}\n")
        
        # Clear previous conversation
        self.agent.clear_conversation()
        self.conversation_history = []
        self.test_results = []
        
        # Run through the dataset
        for i, item in enumerate(dataset):
            print(f"\n[Message {i+1}/{len(dataset)}]")
            self.simulate_message(item["message"], metadata=item)
            
            # Add delay between messages for better readability
            if i < len(dataset) - 1:  # Don't delay after the last message
                time.sleep(delay)
        
        # Print summary
        self._print_conversation_summary()
    
    def run_all_datasets(self, delay: float = 1.0):
        """Run all conversation datasets"""
        all_results = {}
        
        for dataset_name in CONVERSATION_DATASETS:
            print(f"\n\n{'#'*80}")
            print(f"# DATASET: {dataset_name}")
            print(f"{'#'*80}")
            
            self.run_conversation_dataset(dataset_name, delay)
            all_results[dataset_name] = self.test_results.copy()
            
            # Pause between datasets
            print("\nPausing before next dataset...")
            time.sleep(3)
        
        # Print overall summary
        self._print_overall_summary(all_results)
    
    def _print_conversation_summary(self):
        """Print a summary of the conversation test results"""
        print(f"\n{'='*60}")
        print("CONVERSATION SUMMARY")
        print(f"{'='*60}")
        
        total_messages = len(self.test_results)
        successful = sum(1 for r in self.test_results if r["success"])
        failed = total_messages - successful
        avg_response_time = sum(r.get("elapsed_time", 0) for r in self.test_results if r["success"]) / max(successful, 1)
        
        print(f"Total messages: {total_messages}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/total_messages)*100:.1f}%")
        print(f"Average response time: {avg_response_time:.2f}s")
        
        if failed > 0:
            print("\nFailed messages:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - [{result['id']}] {result['message'][:50]}... - Error: {result.get('error', 'Unknown')}")
        
        print(f"\nConversation length: {len(self.conversation_history)} messages")
        print(f"{'='*60}\n")
    
    def _print_overall_summary(self, all_results: Dict[str, List[Dict]]):
        """Print an overall summary of all dataset results"""
        print(f"\n\n{'='*80}")
        print("OVERALL TEST SUMMARY")
        print(f"{'='*80}")
        
        for dataset_name, results in all_results.items():
            total = len(results)
            successful = sum(1 for r in results if r["success"])
            print(f"\n{dataset_name}:")
            print(f"  Success rate: {(successful/total)*100:.1f}% ({successful}/{total})")
            
            # Group by expected skill
            skill_stats = {}
            for r in results:
                skill = r.get("expected_skill", "unknown")
                if skill not in skill_stats:
                    skill_stats[skill] = {"total": 0, "success": 0}
                skill_stats[skill]["total"] += 1
                if r["success"]:
                    skill_stats[skill]["success"] += 1
            
            print("  By expected skill:")
            for skill, stats in skill_stats.items():
                success_rate = (stats["success"]/stats["total"])*100
                print(f"    - {skill}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
    
    def save_test_results(self, filename: str = None):
        """Save test results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "conversation_history": self.conversation_history,
            "test_results": self.test_results,
            "agent_memory": self.agent.memory.get_all() if hasattr(self.agent, 'memory') else []
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Test results saved to {filename}")
        print(f"\nTest results saved to: {filename}")
    
    def run_test_scenario(self, scenario_name: str = "basic"):
        """
        Run a predefined test scenario (backwards compatibility)
        
        Args:
            scenario_name: Name of the scenario to run
        """
        # Map old scenarios to new datasets
        scenario_mapping = {
            "basic": "mixed_conversation",
            "search_queries": "product_discovery",
            "mixed_queries": "shopping_journey"
        }
        
        mapped_dataset = scenario_mapping.get(scenario_name, scenario_name)
        if mapped_dataset in CONVERSATION_DATASETS:
            self.run_conversation_dataset(mapped_dataset)
        else:
            logger.error(f"Unknown scenario: {scenario_name}")
            print(f"Try one of these datasets: {', '.join(CONVERSATION_DATASETS.keys())}")
    
    def interactive_mode(self):
        """Run in interactive mode where the user can type messages directly"""
        print("\nE-commerce Agent Interactive Mode")
        print("Type your messages below. Type 'quit', 'exit', or 'q' to exit.")
        print("Type 'image:path_to_image' before your message to include an image.")
        print("Type 'save' to save the conversation history.\n")
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Exiting interactive mode.")
                break
            
            # Check for save command
            if user_input.lower() == 'save':
                self.save_test_results()
                continue
            
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
    parser.add_argument('--dataset', type=str, default=None, 
                        help='Run a specific conversation dataset')
    parser.add_argument('--all-datasets', action='store_true',
                        help='Run all conversation datasets')
    parser.add_argument('--scenario', type=str, default=None, 
                        help='Run a predefined test scenario (legacy)')
    parser.add_argument('--interactive', action='store_true', 
                        help='Run in interactive mode')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug mode')
    parser.add_argument('--message', type=str, default=None, 
                        help='Single message to process')
    parser.add_argument('--image', type=str, default=None, 
                        help='Path to image file to include with message')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between messages in seconds')
    parser.add_argument('--save-results', action='store_true',
                        help='Save test results to file')
    
    args = parser.parse_args()
    
    # Create prototype agent
    prototype = EcommerceAgentPrototype(debug=args.debug)
    
    # Create test_images directory if it doesn't exist
    os.makedirs("test_images", exist_ok=True)
    
    # Determine mode of operation
    if args.all_datasets:
        prototype.run_all_datasets(args.delay)
        if args.save_results:
            prototype.save_test_results()
    elif args.dataset:
        prototype.run_conversation_dataset(args.dataset, args.delay)
        if args.save_results:
            prototype.save_test_results()
    elif args.scenario:
        prototype.run_test_scenario(args.scenario)
    elif args.message:
        prototype.simulate_message(args.message, args.image)
    elif args.interactive:
        prototype.interactive_mode()
    else:
        # Default to showing available datasets
        print("E-commerce Agent Conversation Simulator")
        print("\nAvailable conversation datasets:")
        for name, dataset in CONVERSATION_DATASETS.items():
            print(f"\n  {name}: ({len(dataset)} messages)")
            print(f"    Description: {dataset[0].get('description', 'N/A')}")
        print("\nRun with --dataset <name> to simulate a conversation")
        print("Run with --all-datasets to run all conversations")
        print("Run with --interactive for interactive mode")


if __name__ == "__main__":
    main()
