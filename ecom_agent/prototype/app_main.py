import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple
import gradio as gr
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ecommerce_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ecommerce_agent.integrated_app")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from memory import Memory
from reflection import Reflection
from planner import Planner
from image_processor import ImageProcessor
from product_recommender import ProductRecommender
from skill_integration import SkillIntegration

# Load environment variables
load_dotenv()

class IntegratedEcommerceAgent:
    """Integrated e-commerce agent with all components"""
    
    def __init__(self):
        # Initialize core systems
        self.memory = Memory()
        self.reflection = Reflection()
        self.planner = Planner()
        
        # Initialize specialized components
        self.image_processor = ImageProcessor()
        self.product_recommender = ProductRecommender(self.memory, self.reflection)
        
        # Initialize skill integration
        self.skill_integration = SkillIntegration(self.memory, self.reflection, self.planner)
        
        # Conversation history
        self.conversation_history = []
        
        # Active render request
        self.active_render_request = None
        
        logger.info("IntegratedEcommerceAgent initialized with all components")
    
    def add_to_conversation(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        logger.debug(f"Added to conversation: {role} - {content[:50]}...")
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
        return "Conversation cleared."
    
    def process_query(self, query: str, image: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """Process a user query and return a response"""
        try:
            # Add user message to conversation history
            user_message = {"role": "user", "content": query}
            if image:
                user_message["image"] = image
            self.conversation_history.append(user_message)
            
            # Prepare context for skill determination
            context = {
                "query": query,
                "conversation_history": self.conversation_history
            }
            
            if image:
                context["image_path"] = image
            
            # Determine and execute appropriate skill
            result = self.skill_integration.route_query(query, context)
            
            # Format the response
            response = self._format_response(result)
            
            # Add assistant response to conversation history
            assistant_message = {"role": "assistant", "content": response}
            if "image_path" in result:
                assistant_message["image"] = result["image_path"]
            self.conversation_history.append(assistant_message)
            
            # Return response and any generated/edited image path
            return response, result.get("image_path")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_response = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response, None
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """Format the response based on result type"""
        result_type = result.get("type", "unknown")
        
        if result_type == "chat_response":
            # Return the LLM's response directly
            return result.get("response", "")
        
        elif result_type == "search_results":
            # Format search results
            response = f"Here are the search results for '{result['query']}':\n\n"
            
            if not result.get("results"):
                return "I couldn't find any products matching your search. Please try different search terms."
            
            for i, product in enumerate(result["results"][:5]):  # Show top 5 results
                response += f"{i+1}. {product['name']} - ${product['price']} (Rating: {product['rating']})\n"
                if "description" in product:
                    response += f"   {product['description']}\n"
            
            if len(result["results"]) > 5:
                response += f"\nFound {len(result['results'])} products in total."
        
        elif result_type == "order_confirmation":
            # Format order confirmation
            response = f"Your order has been placed!\n\n"
            response += f"Order ID: {result['order_id']}\n"
            response += f"Product: {result['product']['name']}\n"
            response += f"Quantity: {result.get('quantity', 1)}\n"
            response += f"Total: ${result['order_details']['total']}\n"
            response += f"Status: {result['status']}"
        
        elif result_type == "order_details":
            # Format order details
            order = result["order"]
            response = f"Here are the details for order {order['order_id']}:\n\n"
            response += f"Date: {order['date']}\n"
            response += f"Product: {order['product']['name']}\n"
            response += f"Total: ${order['total']}\n"
            response += f"Status: {order['status']}\n"
            
            if "status_details" in order:
                response += f"\n{order['status_details']}\n"
            
            if "estimated_delivery" in order:
                from datetime import datetime
                try:
                    delivery_date = datetime.fromisoformat(order['estimated_delivery']).strftime("%B %d, %Y")
                    response += f"\nEstimated delivery: {delivery_date}"
                except:
                    response += f"\nEstimated delivery: {order['estimated_delivery']}"
        
        elif result_type == "order_cancellation":
            # Format cancellation confirmation
            response = f"Your order {result['order_id']} has been cancelled.\n\n"
            response += f"Cancellation ID: {result['cancellation_id']}\n"
            response += f"Reason: {result['reason']}\n"
            response += f"Refund Amount: ${result['refund_amount']}\n"
            response += f"Refund Method: {result['refund_method']}\n"
            
            if "estimated_refund_date" in result:
                from datetime import datetime
                try:
                    refund_date = datetime.fromisoformat(result['estimated_refund_date']).strftime("%B %d, %Y")
                    response += f"Estimated refund date: {refund_date}"
                except:
                    response += f"Estimated refund date: {result['estimated_refund_date']}"
        
        elif result_type == "image_generation":
            # Format image generation response
            response = f"I've generated an image based on your request.\n"
            if "description" in result:
                response += f"\n{result['description']}\n"
            response += "\nYou can see the generated image below."
        
        elif result_type == "image_editing":
            # Format image editing response
            response = f"I've edited the image based on your request.\n"
            if "description" in result:
                response += f"\n{result['description']}\n"
            response += "\nYou can see the edited image below."
        
        elif result_type.endswith("_error"):
            # Format error response
            response = f"Sorry, I encountered an issue: {result.get('error', 'Unknown error')}"
            if "reason" in result:
                response += f"\nReason: {result['reason']}"
        
        else:
            # For unknown types, return the response directly if it exists
            response = result.get("response", "")
        
        return response

def create_interface():
    """Create the Gradio interface for the integrated e-commerce agent"""
    # Initialize the agent
    agent = IntegratedEcommerceAgent()
    logger.info("Creating Gradio interface")
    
    # Define Gradio interface
    with gr.Blocks(title="E-commerce Assistant") as demo:
        gr.Markdown("# E-commerce Assistant")
        gr.Markdown("Ask questions, search for products, place orders, and more!")
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Conversation", height=400, type="messages")
                
                with gr.Row():
                    user_input = gr.Textbox(label="Your Query", placeholder="Ask something...", lines=2)
                    image_input = gr.Image(label="Upload Image (Optional)", type="filepath")
                
                with gr.Row():
                    submit_btn = gr.Button("Submit")
                    clear_btn = gr.Button("Clear Conversation")
            
            with gr.Column(scale=1):
                memory_display = gr.JSON(label="Agent Memory", value=[])
                view_memory_btn = gr.Button("View Memory")
                
                # Add an image output for rendered products
                rendered_image = gr.Image(label="Rendered Product", visible=False)
        
        def user_query(message, image):
            logger.debug(f"User query function called with message: {message}")
            if not message and not image: # Allow image-only queries
                 logger.warning("Empty query and no image submitted")
                 # Return current history without adding anything
                 return "", agent.get_conversation_history(), gr.update(visible=False), None

            # Process the image path if provided
            image_path = None
            if image:
                # Ensure the image path is absolute
                image_path = os.path.abspath(image)
                logger.info(f"Processing image at path: {image_path}")
            
            # Use a default query if only an image is provided
            query_text = message if message else "Analyze this image."

            response, rendered_image_path = agent.process_query(query_text, image_path)
            logger.debug(f"Response generated: {response[:50]}...")
            
            # Get the full conversation history
            updated_history = agent.get_conversation_history()
            
            # Show rendered image if available
            if rendered_image_path:
                logger.info(f"Showing rendered image: {rendered_image_path}")
                # Add the rendered image to the assistant's last message if not already present
                if updated_history and updated_history[-1]['role'] == 'assistant':
                    if 'image' not in updated_history[-1] or updated_history[-1]['image'] != rendered_image_path:
                         # This part might need adjustment depending on how process_query returns rendered images
                         # Assuming process_query already added it correctly to history. If not, uncomment below:
                         # updated_history[-1]['image'] = rendered_image_path
                         pass # Assuming process_query handles adding image to history

                return "", updated_history, gr.update(visible=True, value=rendered_image_path), rendered_image_path
            else:
                # Return empty string for user input, the updated history, and hide the rendered image component
                return "", updated_history, gr.update(visible=False), None
        
        def view_memory():
            logger.debug("View memory function called")
            return agent.memory.get_all()
        
        def clear_conversation():
            logger.debug("Clear conversation function called")
            agent.clear_conversation()
            # Return empty lists for chatbot and memory display
            return [], []
        
        # Set up event handlers
        submit_btn.click(
            user_query,
            inputs=[user_input, image_input],
            # Update chatbot output to receive the full history
            outputs=[user_input, chatbot, rendered_image, rendered_image] 
        )
        
        view_memory_btn.click(
            view_memory,
            inputs=[],
            outputs=[memory_display]
        )
        
        clear_btn.click(
            clear_conversation,
            inputs=[],
            # Update chatbot and memory display on clear
            outputs=[chatbot, memory_display] 
        )
    
    logger.info("Gradio interface created")
    return demo

if __name__ == "__main__":
    # Create directories
    os.makedirs("rendered_products", exist_ok=True)
    
    # Log system information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        # Create and launch the interface
        logger.info("Starting integrated e-commerce agent")
        demo = create_interface()
        demo.launch(
            server_name="0.0.0.0",  # Listen on all network interfaces
            server_port=7860,       # Use the standard Gradio port
            share=True,             # Create a shareable link
            queue=False             # Disable the queue system to fix 405 errors
        )
        logger.info("Integrated e-commerce agent is running")
    except Exception as e:
        logger.error(f"Error launching interface: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
