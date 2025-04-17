import os
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
    
    def analyze_user_image(self, image_path: str, query: str = "") -> Dict[str, Any]:
        """Analyze a user-provided image using GPT-4 Vision"""
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Use OpenAI to analyze the image
        analysis_result = self.openai_helper.analyze_image(image_path, query)
        
        if not analysis_result["success"]:
            return {"error": f"Failed to analyze image: {analysis_result['error']}"}
        
        # Store the analysis in memory if available
        analysis = {
            "image_path": image_path,
            "analysis": analysis_result["analysis"],
            "query": query
        }
        
        if self.memory_system:
            self.memory_system.add("image_analysis", analysis)
        
        return analysis
    
    def generate_recommendations(self, image_path: str, query: str) -> Dict[str, Any]:
        """Generate product recommendations using GPT-4"""
        # First analyze the image
        image_analysis = self.analyze_user_image(image_path, query)
        if "error" in image_analysis:
            return image_analysis
        
        # Generate recommendations using OpenAI
        recommendations_result = self.openai_helper.generate_product_recommendations(
            image_analysis["analysis"],
            query
        )
        
        if not recommendations_result["success"]:
            return {"error": f"Failed to generate recommendations: {recommendations_result['error']}"}
        
        # Store recommendations in memory if available
        recommendations = {
            "image_path": image_path,
            "query": query,
            "recommendations": recommendations_result["recommendations"]
        }
        
        if self.memory_system:
            self.memory_system.add("product_recommendations", recommendations)
        
        return recommendations
    
    def ask_for_rendering(self, image_path: str, recommendations: Dict[str, Any]) -> Tuple[str, str]:
        """Ask if user wants to see a product rendering"""
        if "error" in recommendations:
            return recommendations["error"], None
        
        # Generate a rendering prompt using OpenAI
        prompt_result = self.openai_helper.generate_product_rendering_prompt(
            recommendations["analysis"],
            recommendations["recommendations"]
        )
        
        if not prompt_result["success"]:
            return "I couldn't generate a rendering prompt. Here are the recommendations without visualization.", None
        
        # Store the render request
        request_id = f"render_{len(self.render_requests)}"
        self.render_requests[request_id] = {
            "image_path": image_path,
            "prompt": prompt_result["prompt"],
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
            request["recommendations"]["recommendations"],
            request["prompt"]
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
