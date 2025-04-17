import os
import json
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from openai_integration import OpenAIHelper
from gemini_integration import GeminiHelper

class ProductRecommender:
    """Product recommendation system with image rendering capabilities"""
    
    def __init__(self, memory_system=None, reflection_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.render_requests = {}
        self.openai_helper = OpenAIHelper()
        self.gemini_helper = GeminiHelper()
        self.product_database = self._load_product_database()
    
    def _load_product_database(self) -> List[Dict[str, Any]]:
        """Load the product database"""
        try:
            if os.path.exists("product_database.json"):
                with open("product_database.json", "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading product database: {str(e)}")
            return []
    
    def analyze_user_image(self, image_path: str, query: str = "") -> Dict[str, Any]:
        """Analyze a user-provided image using GPT-4 Vision"""
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Use OpenAI to analyze the image
        analysis_result = self.openai_helper.vision_completion(image_path, query)
        
        if not analysis_result["success"]:
            return {"error": f"Failed to analyze image: {analysis_result['error']}"}
        
        # Store the analysis in memory if available
        analysis = {
            "image_path": image_path,
            "analysis": analysis_result["content"],
            "query": query
        }
        
        if self.memory_system:
            self.memory_system.add("image_analysis", analysis)
        
        return analysis
    
    def generate_recommendations(self, image_path: str, query: str) -> Dict[str, Any]:
        """Generate product recommendations using GPT-4 and product database"""
        # First analyze the image
        image_analysis = self.analyze_user_image(image_path, query)
        if "error" in image_analysis:
            return image_analysis
        
        # Get product recommendations from OpenAI
        recommendations_result = self.openai_helper.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a product recommendation system. Based on the image analysis and query, recommend products from our database.
                    Available products: {json.dumps(self.product_database)}
                    Format your response as a JSON array of product IDs that match the user's needs."""
                },
                {
                    "role": "user",
                    "content": f"Image Analysis: {image_analysis['analysis']}\nUser Query: {query}"
                }
            ]
        )
        
        if not recommendations_result["success"]:
            return {"error": f"Failed to generate recommendations: {recommendations_result['error']}"}
        
        try:
            # Parse the recommended product IDs
            recommended_ids = json.loads(recommendations_result["content"])
            recommended_products = [
                product for product in self.product_database 
                if product["id"] in recommended_ids
            ]
            
            # Store recommendations in memory if available
            recommendations = {
                "image_path": image_path,
                "query": query,
                "recommendations": recommended_products
            }
            
            if self.memory_system:
                self.memory_system.add("product_recommendations", recommendations)
            
            return recommendations
            
        except json.JSONDecodeError:
            return {"error": "Failed to parse product recommendations"}
    
    def ask_for_rendering(self, image_path: str, recommendations: Dict[str, Any]) -> Tuple[str, str]:
        """Ask if user wants to see a product rendering"""
        if "error" in recommendations:
            return recommendations["error"], None
        
        # Store the render request
        request_id = f"render_{len(self.render_requests)}"
        self.render_requests[request_id] = {
            "image_path": image_path,
            "recommendations": recommendations
        }
        
        message = "I can create a visualization of how these products would look in your image. Would you like to see that?"
        return message, request_id
    
    def create_product_rendering(self, request_id: str) -> Tuple[str, Dict[str, Any]]:
        """Create a product rendering using Gemini"""
        if request_id not in self.render_requests:
            return None, {"error": f"Invalid render request ID: {request_id}"}
        
        request = self.render_requests[request_id]
        
        # Use Gemini to edit the image with the product
        image_path, result = self.gemini_helper.edit_product_in_image(
            request["image_path"],
            request["recommendations"]["recommendations"][0]["description"],  # Use first recommended product
            "Please show how this product would look in the image"
        )
        
        if not result["success"]:
            return None, {"error": f"Failed to create rendering: {result['error']}"}
        
        return image_path, result
    
    def generate_product_image(self, product_description: str) -> Tuple[str, Dict[str, Any]]:
        """Generate a product image using Gemini"""
        image_path, result = self.gemini_helper.generate_product_image(product_description)
        
        if not result["success"]:
            return None, {"error": f"Failed to generate product image: {result['error']}"}
        
        return image_path, result
    
    def generate_product_variations(self, product_description: str, num_variations: int = 3) -> Tuple[List[str], Dict[str, Any]]:
        """Generate multiple variations of a product image"""
        variations, result = self.gemini_helper.generate_product_variations(
            product_description,
            num_variations
        )
        
        if not result["success"]:
            return [], {"error": f"Failed to generate variations: {result['error']}"}
        
        return variations, result
