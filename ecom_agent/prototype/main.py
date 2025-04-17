import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from memory import Memory
from reflection import Reflection
from planner import Planner
from router import Router
from image_processor import ImageProcessor
from product_recommender import ProductRecommender

# Load environment variables
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not set in .env file. Image processing features will not work.")

class EcommerceSkills:
    """Implementation of e-commerce skills"""
    
    def __init__(self, memory, reflection, planner):
        self.memory = memory
        self.reflection = reflection
        self.planner = planner
        self.image_processor = ImageProcessor()
        self.product_recommender = ProductRecommender(memory, reflection)
        
    def search_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for products"""
        # Create a plan for this task
        task_id = f"search_{len(self.planner.plans) + 1}"
        plan = self.planner.create_plan(task_id, f"Search for products: {query}", context)
        
        # Execute the plan steps
        self.planner.update_step(task_id, 0, "completed", {"query": query})
        
        # Identify product categories and filters
        categories = []
        filters = {}
        
        # Simple keyword extraction
        keywords = ["shirt", "dress", "pants", "shoes", "electronics", "furniture"]
        for keyword in keywords:
            if keyword in query.lower():
                categories.append(keyword)
        
        self.planner.update_step(task_id, 1, "completed", {"categories": categories, "filters": filters})
        
        # Simulate search execution
        search_results = [
            {"id": 1, "name": "Product 1", "price": 29.99, "rating": 4.5},
            {"id": 2, "name": "Product 2", "price": 39.99, "rating": 4.2},
            {"id": 3, "name": "Product 3", "price": 19.99, "rating": 4.8}
        ]
        
        self.planner.update_step(task_id, 2, "completed", {"results_count": len(search_results)})
        
        # Process results
        sorted_results = sorted(search_results, key=lambda x: x["rating"], reverse=True)
        self.planner.update_step(task_id, 3, "completed", {"sorted_results": sorted_results})
        
        # Prepare response
        response = {
            "type": "search_results",
            "query": query,
            "categories": categories,
            "filters": filters,
            "results": sorted_results,
            "plan": plan
        }
        
        # Add to memory
        self.memory.add("search_results", response)
        
        # Self-reflection
        action = f"Search for products with query: {query}"
        reflection = self.reflection.reflect(action, response, context)
        response["reflection"] = reflection
        
        # Complete the final step
        self.planner.update_step(task_id, 4, "completed", {"response_prepared": True})
        
        return response
    
    def place_order_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order"""
        # Create a plan for this task
        task_id = f"order_{len(self.planner.plans) + 1}"
        plan = self.planner.create_plan(task_id, f"Place an order: {query}", context)
        
        # Execute the plan steps
        self.planner.update_step(task_id, 0, "completed", {"query": query})
        
        # Simulate product identification
        product = {"id": 1, "name": "Product 1", "price": 29.99}
        self.planner.update_step(task_id, 1, "completed", {"product": product, "available": True})
        
        # Simulate shipping information collection
        shipping = {"address": "123 Main St", "city": "Anytown", "zip": "12345"}
        self.planner.update_step(task_id, 2, "completed", {"shipping": shipping})
        
        # Simulate payment information collection
        payment = {"method": "Credit Card", "last4": "1234"}
        self.planner.update_step(task_id, 3, "completed", {"payment": payment})
        
        # Simulate order confirmation
        order_details = {
            "product": product,
            "shipping": shipping,
            "payment": payment,
            "total": product["price"] + 5.99  # Adding shipping
        }
        self.planner.update_step(task_id, 4, "completed", {"order_details": order_details})
        
        # Simulate order processing
        order_id = "ORD-" + str(1000 + len(self.planner.plans))
        self.planner.update_step(task_id, 5, "completed", {"order_id": order_id})
        
        # Prepare response
        response = {
            "type": "order_confirmation",
            "order_id": order_id,
            "product": product,
            "shipping": shipping,
            "payment": payment,
            "total": order_details["total"],
            "status": "confirmed",
            "plan": plan
        }
        
        # Add to memory
        self.memory.add("order", response)
        
        # Self-reflection
        action = f"Place order for product: {product['name']}"
        reflection = self.reflection.reflect(action, response, context)
        response["reflection"] = reflection
        
        # Complete the final step
        self.planner.update_step(task_id, 6, "completed", {"confirmation_sent": True})
        
        return response
    
    def search_order_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for an order"""
        # Create a plan for this task
        task_id = f"search_order_{len(self.planner.plans) + 1}"
        plan = self.planner.create_plan(task_id, f"Search for order: {query}", context)
        
        # Execute the plan steps
        self.planner.update_step(task_id, 0, "completed", {"query": query})
        
        # Simulate order retrieval
        order_id = "ORD-1001"  # Default order ID
        
        # Extract order ID from query if present
        import re
        order_id_match = re.search(r'ORD-\d+', query)
        if order_id_match:
            order_id = order_id_match.group(0)
        
        self.planner.update_step(task_id, 1, "completed", {"order_id": order_id})
        
        # Simulate order details retrieval
        order_details = {
            "order_id": order_id,
            "date": "2025-04-15",
            "product": {"id": 1, "name": "Product 1", "price": 29.99},
            "shipping": {"address": "123 Main St", "city": "Anytown", "zip": "12345"},
            "payment": {"method": "Credit Card", "last4": "1234"},
            "total": 35.98,
            "status": "shipped"
        }
        
        self.planner.update_step(task_id, 2, "completed", {"status": order_details["status"]})
        
        # Prepare response
        response = {
            "type": "order_details",
            "query": query,
            "order": order_details,
            "plan": plan
        }
        
        # Add to memory
        self.memory.add("order_search", response)
        
        # Self-reflection
        action = f"Search for order: {order_id}"
        reflection = self.reflection.reflect(action, response, context)
        response["reflection"] = reflection
        
        # Complete the final step
        self.planner.update_step(task_id, 3, "completed", {"response_prepared": True})
        
        return response
    
    def cancel_order_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an order"""
        # Create a plan for this task
        task_id = f"cancel_order_{len(self.planner.plans) + 1}"
        plan = self.planner.create_plan(task_id, f"Cancel order: {query}", context)
        
        # Execute the plan steps
        self.planner.update_step(task_id, 0, "completed", {"query": query})
        
        # Simulate order identification
        order_id = "ORD-1001"  # Default order ID
        
        # Extract order ID from query if present
        import re
        order_id_match = re.search(r'ORD-\d+', query)
        if order_id_match:
            order_id = order_id_match.group(0)
        
        # Simulate eligibility check
        eligible = True
        reason = "Order is within cancellation window"
        
        self.planner.update_step(task_id, 1, "completed", {"eligible": eligible, "reason": reason})
        
        # Simulate cancellation processing
        cancellation_id = "CAN-" + order_id[4:]
        self.planner.update_step(task_id, 2, "completed", {"cancellation_id": cancellation_id})
        
        # Prepare response
        response = {
            "type": "order_cancellation",
            "query": query,
            "order_id": order_id,
            "cancellation_id": cancellation_id,
            "status": "cancelled",
            "refund_amount": 35.98,
            "refund_method": "Credit Card",
            "plan": plan
        }
        
        # Add to memory
        self.memory.add("order_cancellation", response)
        
        # Self-reflection
        action = f"Cancel order: {order_id}"
        reflection = self.reflection.reflect(action, response, context)
        response["reflection"] = reflection
        
        # Complete the final step
        self.planner.update_step(task_id, 3, "completed", {"confirmation_sent": True})
        
        return response
    
    def recommendation_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide product recommendations"""
        # Create a plan for this task
        task_id = f"recommend_{len(self.planner.plans) + 1}"
        plan = self.planner.create_plan(task_id, f"Product recommendation: {query}", context)
        
        # Execute the plan steps
        self.planner.update_step(task_id, 0, "completed", {"query": query})
        
        # Check if image is provided
        image_path = context.get("image_path")
        
        if image_path and os.path.exists(image_path):
            # Process the image
            analysis = self.product_recommender.analyze_user_image(image_path, query)
            self.planner.update_step(task_id, 1, "completed", {"image_analyzed": True, "analysis": analysis})
            
            # Generate recommendations
            recommendations = self.product_recommender.generate_recommendations(image_path, query)
            self.planner.update_step(task_id, 2, "completed", {"recommendations_generated": True})
            
            # Check if user wants image rendering
            render_message, request_id = self.product_recommender.ask_for_rendering(image_path, recommendations)
            self.planner.update_step(task_id, 3, "completed", {"render_requested": True, "request_id": request_id})
            
            # Prepare response
            response = {
                "type": "product_recommendation",
                "query": query,
                "image_based": True,
                "analysis": analysis,
                "recommendations": recommendations,
                "render_message": render_message,
                "render_request_id": request_id,
                "plan": plan
            }
        else:
            # Text-based recommendations
            self.planner.update_step(task_id, 1, "completed", {"image_analyzed": False})
            
            # Simulate recommendation generation
            recommendations = [
                {"id": 1, "name": "Recommended Product 1", "price": 29.99, "rating": 4.8},
                {"id": 2, "name": "Recommended Product 2", "price": 39.99, "rating": 4.6},
                {"id": 3, "name": "Recommended Product 3", "price": 19.99, "rating": 4.9}
            ]
            
            self.planner.update_step(task_id, 2, "completed", {"recommendations_generated": True})
            self.planner.update_step(task_id, 3, "completed", {"render_requested": False})
            self.planner.update_step(task_id, 4, "completed", {"render_created": False})
            
            # Prepare response
            response = {
                "type": "product_recommendation",
                "query": query,
                "image_based": False,
                "recommendations": recommendations,
                "plan": plan
            }
        
        # Add to memory
        self.memory.add("recommendation", response)
        
        # Self-reflection
        action = f"Generate product recommendations for query: {query}"
        reflection = self.reflection.reflect(action, response, context)
        response["reflection"] = reflection
        
        # Complete the final step
        self.planner.update_step(task_id, 5, "completed", {"response_prepared": True})
        
        return response
    
    def process_render_response(self, request_id: str, user_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user response to rendering request"""
        # Get the rendering request
        request = self.product_recommender.get_rendering_request(request_id)
        
        if "error" in request:
            return {"error": request["error"]}
        
        # Check user response
        if user_response.lower() in ["yes", "y", "sure", "ok", "okay"]:
            # Create the rendering
            recommendations = request["recommendations"]
            product_description = None
            
            if "recommendations" in recommendations:
                # Extract first product from recommendations
                recommendation_text = recommendations["recommendations"]
                lines = recommendation_text.split("\n")
                if lines:
                    product_description = lines[0]
            
            # Create the rendering
            rendered_image_path, result = self.product_recommender.create_product_rendering(request_id, product_description)
            
            # Prepare response
            response = {
                "type": "product_rendering",
                "request_id": request_id,
                "rendered_image_path": rendered_image_path,
                "result": result
            }
            
            # Add to memory
            self.memory.add("rendering_result", response)
            
            return response
        else:
            # User declined rendering
            response = {
                "type": "rendering_declined",
                "request_id": request_id,
                "message": "You've declined the product rendering. Here are the recommendations without visualization."
            }
            
            # Add to memory
            self.memory.add("rendering_declined", response)
            
            return response

class EcommerceAgent:
    """Main e-commerce agent class"""
    
    def __init__(self):
        # Initialize components
        self.memory = Memory()
        self.reflection = Reflection()
        self.planner = Planner()
        self.router = Router()
        
        # Initialize skills
        self.skills = EcommerceSkills(self.memory, self.reflection, self.planner)
        
        # Register skills with router
        self.router.register_skill("search", self.skills.search_skill, ["search", "find", "look for"])
        self.router.register_skill("place_order", self.skills.place_order_skill, ["place order", "buy", "purchase"])
        self.router.register_skill("search_order", self.skills.search_order_skill, ["find order", "order status", "track"])
        self.router.register_skill("cancel_order", self.skills.cancel_order_skill, ["cancel order", "return"])
        self.router.register_skill("recommendation", self.skills.recommendation_skill, ["recommend", "suggest"])
        
        # Conversation history
        self.conversation_history = []
        
        # Active render request
        self.active_render_request = None
    
    def add_to_conversation(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        return "Conversation cleared."
    
    def process_query(self, query, image=None):
        """Process a user query"""
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
                
            result = self.skills.process_render_response(request_id, query, context)
            
            if "error" in result:
                response = f"Sorry, there was an error processing your response: {result['error']}"
            elif result["type"] == "product_rendering":
                response = f"I've created a visualization of the recommended product on your image. You can see how it would look!"
                # Add the rendered image path to the result for the UI to display
                return response, result["rendered_image_path"]
            else:
                response = result["message"]
            
            self.add_to_conversation("assistant", response)
            return response, None
        
        # Prepare context
        context = {"query": query}
        if image:
            context["image_path"] = image
            # Add image to memory
            self.memory.add("user_image", {"path": image})
        
        # Route the query
        skill_name, result = self.router.route(query, context)
        
        if result is None:
            # No skill matched, provide a default response
            response = "I'm not sure how to help with that. Could you please try asking about searching for products, placing an order, checking an order status, or getting product recommendations?"
        else:
            # Process the skill result
            if skill_name == "recommendation" and result.get("render_message") and result.get("render_request_id"):
                # Store the active render request
                self.active_render_request = result["render_request_id"]
                response = result["render_message"]
            elif skill_name == "search":
                # Format search results
                response = f"Here are the search results for '{result['query']}':\n\n"
                for i, product in enumerate(result["results"]):
                    response += f"{i+1}. {product['name']} - ${product['price']} (Rating: {product['rating']})\n"
            elif skill_name == "place_order":
                # Format order confirmation
                response = f"Your order has been placed!\n\n"
                response += f"Order ID: {result['order_id']}\n"
                response += f"Product: {result['product']['name']}\n"
                response += f"Total: ${result['total']}\n"
                response += f"Status: {result['status']}"
            elif skill_name == "search_order":
                # Format order details
                order = result["order"]
                response = f"Here are the details for order {order['order_id']}:\n\n"
                response += f"Date: {order['date']}\n"
                response += f"Product: {order['product']['name']}\n"
                response += f"Total: ${order['total']}\n"
                response += f"Status: {order['status']}"
            elif skill_name == "cancel_order":
                # Format cancellation confirmation
                response = f"Your order {result['order_id']} has been cancelled.\n\n"
                response += f"Cancellation ID: {result['cancellation_id']}\n"
                response += f"Refund Amount: ${result['refund_amount']}\n"
                response += f"Refund Method: {result['refund_method']}"
            else:
                # Generic response
                response = f"Processed your request: {query}"
        
        # Add response to conversation history
        self.add_to_conversation("assistant", response)
        
        return response, None

# Create the Gradio interface
def create_interface():
    # Initialize the agent
    agent = EcommerceAgent()
    
    # Define Gradio interface
    with gr.Blocks(title="E-commerce Assistant") as demo:
        gr.Markdown("# E-commerce Assistant")
        gr.Markdown("Ask questions, search for products, place orders, and more!")
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Conversation", height=400)
                
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
            if not message.strip():
                return "Please enter a query.", chatbot, memory_display, gr.update(visible=False), None
            
            response, rendered_image_path = agent.process_query(message, image)
            
            # Update chatbot with user message and response
            conversation = chatbot + [[message, response]]
            
            # Show rendered image if available
            if rendered_image_path:
                return "", conversation, memory_display, gr.update(visible=True), rendered_image_path
            else:
                return "", conversation, memory_display, gr.update(visible=False), None
        
        def view_memory():
            return agent.memory.get_all()
        
        def clear_conversation():
            agent.clear_conversation()
            return [], []
        
        # Set up event handlers
        submit_btn.click(
            user_query,
            inputs=[user_input, image_input],
            outputs=[user_input, chatbot, memory_display, rendered_image, rendered_image]
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
    
    return demo

if __name__ == "__main__":
    # Create directories
    os.makedirs("rendered_products", exist_ok=True)
    
    # Create and launch the interface
    demo = create_interface()
    demo.launch(share=True)
