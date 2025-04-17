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
    
    def process_query(self, query, image=None):
        logger.info(f"Processing query: {query}")
        if image:
            logger.info(f"Image provided: {image}")
        
        try:
            # Add query to conversation history
            self.add_to_conversation("user", query)
            
            # Check if this is a response to a render request
            if self.active_render_request:
                request_id = self.active_render_request
                self.active_render_request = None
                
                # Process the render response
                context = {"query": query}
                if image:
                    context["image_path"] = image
                    
                if query.lower() in ["yes", "y", "sure", "ok", "okay"]:
                    # Create the rendering
                    logger.info(f"Creating product rendering for request: {request_id}")
                    rendered_image_path, result = self.product_recommender.create_product_rendering(request_id)
                    
                    response = f"I've created a visualization of the recommended product on your image. You can see how it would look!"
                    self.add_to_conversation("assistant", response)
                    return response, rendered_image_path
                else:
                    # User declined rendering
                    logger.info(f"User declined product rendering for request: {request_id}")
                    response = "You've declined the product rendering. Here are the recommendations without visualization."
                    self.add_to_conversation("assistant", response)
                    return response, None
            
            # Prepare context
            context = {"query": query}
            if image:
                context["image_path"] = image
                # Add image to memory
                self.memory.add("user_image", {"path": image})
            
            # Check if this is a product recommendation request with an image
            if image and ("recommend" in query.lower() or "suggest" in query.lower()):
                logger.info("Processing as product recommendation with image")
                # Analyze the image
                analysis = self.product_recommender.analyze_user_image(image, query)
                
                # Generate recommendations
                recommendations = self.product_recommender.generate_recommendations(image, query)
                
                # Ask if user wants a rendering
                render_message, request_id = self.product_recommender.ask_for_rendering(image, recommendations)
                
                # Store the active render request
                self.active_render_request = request_id
                
                # Add response to conversation history
                self.add_to_conversation("assistant", render_message)
                
                return render_message, None
            
            # Route the query to the appropriate skill
            logger.info("Routing query to appropriate skill")
            result = self.skill_integration.route_query(query, context)
            
            # Format the response based on result type
            response = self._format_response(result)
            
            # Add response to conversation history
            self.add_to_conversation("assistant", response)
            
            return response, None
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            error_response = f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your query."
            self.add_to_conversation("assistant", error_response)
            return error_response, None
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """Format the response based on result type"""
        result_type = result.get("type", "unknown")
        
        if result_type == "search_results":
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
        
        elif result_type.endswith("_error"):
            # Format error response
            response = f"Sorry, I encountered an issue: {result.get('error', 'Unknown error')}"
            if "reason" in result:
                response += f"\nReason: {result['reason']}"
        
        else:
            # Generic response
            response = f"I've processed your request: {result.get('query', '')}"
            if "error" in result:
                response = f"Sorry, there was an error: {result['error']}"
        
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
            if not message.strip():
                logger.warning("Empty query submitted")
                return "Please enter a query.", [], gr.update(visible=False), None
            
            response, rendered_image_path = agent.process_query(message, image)
            logger.debug(f"Response generated: {response[:50]}...")
            
            # Create a new messages list with the latest interaction in the correct format
            new_history = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
            
            # Show rendered image if available
            if rendered_image_path:
                logger.info(f"Showing rendered image: {rendered_image_path}")
                return "", new_history, gr.update(visible=True), rendered_image_path
            else:
                return "", new_history, gr.update(visible=False), None
        
        def view_memory():
            logger.debug("View memory function called")
            return agent.memory.get_all()
        
        def clear_conversation():
            logger.debug("Clear conversation function called")
            agent.clear_conversation()
            return [], []
        
        # Set up event handlers
        submit_btn.click(
            user_query,
            inputs=[user_input, image_input],
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
