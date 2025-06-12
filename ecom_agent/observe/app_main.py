import os
import sys
import logging
import base64
from typing import Dict, Any, Optional, Tuple, List
import gradio as gr
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from opentelemetry import trace
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, EvalTag, EvalName, EvalTagType, EvalSpanKind, SpanAttributes, FiSpanKindValues

load_dotenv()

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="ecom_agent_observe",
    session_name="ecom_agent_observe",
)

trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

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
# from image_processor import ImageProcessor # Assuming this might not be needed if recommender is gone?
# from product_recommender import ProductRecommender # Remove import
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
        # self.image_processor = ImageProcessor() # Remove/comment out if only used by recommender
        # self.product_recommender = ProductRecommender(self.memory, self.reflection) # Remove instance
        
        # Initialize skill integration
        # Pass None for systems if they aren't used by remaining skills directly
        self.skill_integration = SkillIntegration(self.memory, self.reflection, self.planner)
        
        # Conversation history
        self.conversation_history = []
        # Add state for pending order confirmation
        self.pending_order_context = None 
        
        # Active render request (Is this still needed? Check ProductRecommender usage)
        # Let's remove it for now as it was part of ProductRecommender logic
        # self.active_render_request = None 
        
        logger.info("IntegratedEcommerceAgent initialized (without ProductRecommender)")
    
    def get_image_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 string for span attributes."""
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image file does not exist: {image_path}")
                return None
            
            with open(image_path, "rb") as image_file:
                # Read the raw image data and encode as base64
                image_data = image_file.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
                logger.debug(f"Converted image to base64: {image_path} ({len(base64_string)} chars)")
                return base64_string
                
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return None
    
    def create_product_composite_image(self, image_paths: List[str], products: List[Dict[str, Any]]) -> Optional[str]:
        """Create a composite image showing multiple products in a grid layout."""
        try:
            if not image_paths:
                return None
            
            # Create output directory
            os.makedirs("rendered_products", exist_ok=True)
            
            # Load images
            images = []
            for path in image_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    # Resize to standard size
                    img = img.resize((300, 300), Image.Resampling.LANCZOS)
                    images.append(img)
            
            if not images:
                return None
            
            # Calculate grid dimensions
            num_images = len(images)
            if num_images == 1:
                cols, rows = 1, 1
            elif num_images == 2:
                cols, rows = 2, 1
            elif num_images <= 4:
                cols, rows = 2, 2
            else:
                cols, rows = 3, 2  # Max 6 images
                images = images[:6]
            
            # Create composite image
            img_width, img_height = 300, 300
            padding = 20
            composite_width = cols * img_width + (cols + 1) * padding
            composite_height = rows * img_height + (rows + 1) * padding + 100  # Extra space for text
            
            composite = Image.new('RGB', (composite_width, composite_height), color='white')
            draw = ImageDraw.Draw(composite)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            # Add title
            title = f"Search Results ({len(images)} products)"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (composite_width - title_width) // 2
            draw.text((title_x, 10), title, fill='black', font=title_font)
            
            # Place images in grid
            for i, img in enumerate(images):
                row = i // cols
                col = i % cols
                
                x = padding + col * (img_width + padding)
                y = 50 + padding + row * (img_height + padding)
                
                composite.paste(img, (x, y))
                
                # Add product name below image
                if i < len(products):
                    product_name = products[i].get('name', f'Product {i+1}')
                    price = products[i].get('price', 0)
                    text = f"{product_name}\n${price}"
                    
                    # Calculate text position
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_x = x + (img_width - text_width) // 2
                    text_y = y + img_height + 5
                    
                    draw.text((text_x, text_y), text, fill='black', font=font)
            
            # Save composite image
            import time
            timestamp = int(time.time())
            output_path = f"rendered_products/search_results_{timestamp}.png"
            composite.save(output_path)
            
            logger.info(f"Created composite image with {len(images)} products: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating composite image: {str(e)}")
            return None
    
    def add_to_conversation(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        logger.debug(f"Added to conversation: {role} - {content[:50]}...")
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear the conversation history AND pending order context"""
        self.conversation_history = []
        self.pending_order_context = None # Clear pending order on conversation clear
        logger.info("Conversation history and pending order cleared")
        return "Conversation cleared."
    
    def process_query(self, query: str, image: Optional[str] = None) -> Tuple[str, Optional[str]]:
        with tracer.start_as_current_span("process_query", 
            attributes={
                SpanAttributes.INPUT_VALUE: query,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                "llm.input_messages.0.message.role": "user",
                "llm.input_messages.0.message.content": query,
                SpanAttributes.RAW_INPUT: query,
        }) as span:
            """Process a user query and return a response and optional image path"""
            try:
                # --- Check for Pending Order Confirmation --- 
                if self.pending_order_context:
                    logger.info(f"Received response to pending order confirmation: '{query}'")
                    user_confirmation = 'yes' if query.lower().strip() in ['yes', 'y', 'ok', 'okay', 'confirm', 'proceed'] else 'no'
                    
                    # Prepare context for confirmation execution
                    confirmation_context = {
                        "user_confirmation": user_confirmation,
                        "pending_order_context": self.pending_order_context,
                        "query": query, # Pass original query for logging/context perhaps?
                        "conversation_history": self.conversation_history # Pass current history
                    }
                    
                    # Clear the pending state *before* executing
                    logger.debug("Clearing pending order context.")
                    self.pending_order_context = None 
                    
                    # Re-route specifically to handle the confirmation
                    # We force the skill here to ensure it goes back to OrderSkill
                    logger.info(f"Routing confirmation ('{user_confirmation}') back to OrderSkill.")
                    result = self.skill_integration.route_query(query, confirmation_context)
                    # The skill will now handle yes/no and return final confirmation or cancellation message
                    
                else:
                    # --- Standard Query Processing --- 
                    logger.info("Processing standard query (no pending confirmation).")
                    user_message = {"role": "user", "content": query}
                    if image:
                        user_message["image"] = image
                    self.conversation_history.append(user_message)
                    
                    context = {
                        "query": query,
                        "conversation_history": self.conversation_history
                    }
                    if image:
                        context["image_path"] = image
                    
                    result = self.skill_integration.route_query(query, context)
                # --- End Standard/Confirmation Check --- 
                
                # --- Process Result --- 
                response = ""
                image_path_result = None
                
                # Check if confirmation is needed NOW
                if result.get("type") == "needs_order_confirmation":
                    logger.info("Order skill requires user confirmation.")
                    self.pending_order_context = result.get("internal_context")
                    response = result.get("confirmation_prompt", "Please confirm your order.")
                    # No image path expected here
                    logger.debug(f"Stored pending order context: {self.pending_order_context}")
                else:
                    # Format standard responses (including final order confirmation)
                    response = self._format_response(result)
                    image_path_result = result.get("image_path")
                    
                    # Handle images for search results and recommendations - create composite image
                    if result.get("type") == "search_results" and result.get("has_images"):
                        # Collect product images and create composite
                        product_images = []
                        products_with_images = []
                        for product in result.get("results", [])[:6]:  # Show up to 6 images
                            if product.get("image_url") and os.path.exists(product["image_url"]):
                                product_images.append(product["image_url"])
                                products_with_images.append(product)
                        
                        if product_images:
                            # Create composite image
                            composite_path = self.create_product_composite_image(product_images, products_with_images)
                            if composite_path:
                                image_path_result = composite_path
                                logger.info(f"Created composite image with {len(product_images)} products: {composite_path}")
                    elif result.get("type") == "recommendation_result" and result.get("has_images"):
                        product_images = []
                        products_with_images = []
                        for product in result.get("recommendations", []):
                            if product.get("image_url") and os.path.exists(product["image_url"]):
                                product_images.append(product["image_url"])
                                products_with_images.append(product)
                        
                        if product_images:
                            composite_path = self.create_product_composite_image(product_images, products_with_images)
                            if composite_path:
                                image_path_result = composite_path
                                logger.info(f"Created composite image with {len(product_images)} recommendations: {composite_path}")

                # --- Add Assistant Response to History --- 
                assistant_message = {"role": "assistant", "content": response}
                # Add image ONLY if it came from the result (gen/edit/render/composite)
                # Don't add the user's uploaded image to the assistant message
                if image_path_result:
                    assistant_message["image"] = image_path_result
                # Ensure history doesn't grow excessively if needed
                # self.conversation_history = self.conversation_history[-MAX_HISTORY:] 
                self.conversation_history.append(assistant_message)
                
                # Update span with response and image
                span.set_attribute("llm.output_messages.0.message.role", "assistant")
                span.set_attribute("llm.output_messages.0.message.content", response)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, response)
                span.set_attribute(SpanAttributes.RAW_OUTPUT, response)
                
                # Add image attribute if we have one (composite or single)
                if image_path_result:
                    # Convert image to base64 for span attribute (OpenTelemetry requirement)
                    image_base64 = self.get_image_base64(image_path_result)
                    if image_base64:
                        span.set_attribute("llm.outputMessages.0.message.contents.1.messageContent.role", "assistant")
                        span.set_attribute("llm.outputMessages.0.message.contents.1.messageContent.type", "image")
                        span.set_attribute("llm.outputMessages.0.message.contents.1.messageContent.image", image_base64)
                        logger.debug(f"Added base64 image to span: {image_path_result} ({len(image_base64)} chars)")
                    else:
                        logger.warning(f"Failed to convert image to base64: {image_path_result}")

                return response, image_path_result 
                
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                error_response = f"Sorry, I encountered an error: {str(e)}"
                self.conversation_history.append({"role": "assistant", "content": error_response})

                span.set_attribute("error.message", str(e))
                span.set_attribute("llm.output_messages.0.message.role", "assistant")
                span.set_attribute("llm.output_messages.0.message.content", error_response)
                # No image in error case, so no image attribute needed

                # Clear pending context on error too?
                self.pending_order_context = None
                return error_response, None
    
    def _format_response(self, result: Dict[str, Any]) -> str:
        """Format the response based on result type"""
        result_type = result.get("type", "unknown")
        
        if result_type == "chat_response":
            # Return the LLM's response directly
            return result.get("response", "")
        
        elif result_type == "search_results":
            # Format search results with enhanced styling
            response = f"🔍 **Here are the search results for '{result['query']}':**\n\n"
            
            if not result.get("results"):
                return "❌ I couldn't find any products matching your search. Please try different search terms."
            
            for i, product in enumerate(result["results"][:5]):  # Show top 5 results
                # Add emojis and better formatting
                rating_stars = "⭐" * int(product.get('rating', 0))
                response += f"**{i+1}. {product['name']}** - 💰${product['price']} ({rating_stars} {product.get('rating', 'N/A')})\n"
                if "description" in product:
                    response += f"   📝 {product['description']}\n"
                if "colors" in product and product["colors"]:
                    colors_str = ", ".join(product["colors"])
                    response += f"   🎨 Available colors: {colors_str}\n"
                response += "\n"
            
            if len(result["results"]) > 5:
                response += f"📊 Found {len(result['results'])} products in total. Showing top 5 results."
            
            if result.get("has_images"):
                response += "\n\n🖼️ **Product images are shown below.**"
        
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
    agent = IntegratedEcommerceAgent()
    logger.info("Creating Gradio interface")
    
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
            logger.debug(f"User query function called with message: '{message}' and image: {image}")
            
            if not message and not image:
                logger.warning("Empty query and no image submitted")
                # Return the current history formatted for Gradio
                return "", format_history_for_gradio(agent.get_conversation_history()), gr.update(visible=False), None

            image_path = os.path.abspath(image) if image else None
            if image_path:
                logger.info(f"Processing image at path: {image_path}")
            
            query_text = message if message else "Analyze this image."

            response, rendered_image_path = agent.process_query(query_text, image_path)
            logger.debug(f"Agent response: '{response[:50]}...', Rendered image path: {rendered_image_path}")
            
            # --- Add rendered image to history if present --- 
            current_history = agent.get_conversation_history()
            if rendered_image_path and current_history:
                 last_message = current_history[-1]
                 if last_message.get("role") == "assistant":
                      if "image" not in last_message or last_message["image"] != rendered_image_path:
                           logger.info(f"Adding returned rendered_image_path {rendered_image_path} to last assistant message in history.")
                           last_message["image"] = rendered_image_path
                      else:
                           logger.debug("Rendered image path already seems to be in last assistant message.")
                 else:
                      logger.warning("Cannot add rendered_image_path to history: Last message is not from assistant.")
            # --- End rendered image history update ---

            # Format the potentially updated history for Gradio display
            gradio_display_history = format_history_for_gradio(current_history) # Use updated history

            # Handle rendered image display (separate component - keep this for dedicated view)
            rendered_update = gr.update(visible=False)
            if rendered_image_path:
                logger.info(f"Updating separate rendered_image component: {rendered_image_path}")
                rendered_update = gr.update(visible=True, value=rendered_image_path)
            
            # Product images are now embedded as composite images directly in the chat
            logger.info("Product images are embedded as composite images in chat messages")
            
            # Return empty input, formatted history, rendered image update, AND clear image input
            return "", gradio_display_history, rendered_update, gr.update(value=None)

        def format_history_for_gradio(history: list[dict]) -> list[dict]:
            """Formats the internal history list for Gradio Chatbot(type='messages').
               Handles single images including composite product images.
            """
            gradio_history = []
            for i, msg in enumerate(history):
                role = msg.get('role')
                content_text = msg.get('content', '')
                image_path = msg.get('image')

                # Validate role
                if not role or role not in ["user", "assistant"]:
                    logger.warning(f"Skipping history message with invalid/missing role (index {i}): {msg}")
                    continue
                    
                # Ensure content_text is a string
                if not isinstance(content_text, str):
                     logger.warning(f"Converting non-string content to string (index {i}): {content_text}")
                     content_text = str(content_text).strip()
                else:
                     content_text = content_text.strip()

                # Create the gradio message
                gradio_msg = {"role": role, "content": content_text}
                
                # Handle image (single images, composite images, etc.)
                if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                    gradio_msg["image"] = image_path
                    logger.debug(f"Added image to message {i}: {image_path}")

                if content_text is None:
                     logger.error(f"Content became None unexpectedly (index {i}). Skipping message: {msg}")
                     continue
                     
                gradio_history.append(gradio_msg)

            logger.debug(f"Final Gradio history format for messages: {gradio_history}")
            return gradio_history

        def view_memory():
            logger.debug("View memory function called")
            return agent.memory.get_all()
        
        def clear_conversation():
            logger.debug("Clear conversation function called")
            agent.clear_conversation()
            return [], [] # Return empty list for chatbot and memory
        
        # Set up event handlers
        submit_btn.click(
            user_query,
            inputs=[user_input, image_input],
            outputs=[user_input, chatbot, rendered_image, image_input] 
        )
        view_memory_btn.click(view_memory, inputs=[], outputs=[memory_display])
        clear_btn.click(clear_conversation, inputs=[], outputs=[chatbot, memory_display])
    
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
