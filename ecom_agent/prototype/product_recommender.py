import os
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from image_processor import ImageProcessor

class ProductRecommender:
    """Product recommendation system with image rendering capabilities"""
    
    def __init__(self, memory_system=None, reflection_system=None):
        self.image_processor = ImageProcessor()
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.render_requests = {}
    
    def analyze_user_image(self, image_path: str, query: str = "") -> Dict[str, Any]:
        """Analyze a user-provided image"""
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Store the analysis in memory if available
        analysis = self.image_processor.analyze_image(image_path)
        
        if self.memory_system:
            self.memory_system.add("image_analysis", analysis, {"image_path": image_path, "query": query})
        
        return analysis
    
    def generate_recommendations(self, image_path: str, query: str = "") -> Dict[str, Any]:
        """Generate product recommendations based on image and query"""
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Generate recommendations
        recommendations = self.image_processor.generate_product_recommendation(image_path, query)
        
        # Store in memory if available
        if self.memory_system:
            self.memory_system.add("product_recommendations", recommendations, {"image_path": image_path, "query": query})
        
        # Perform self-reflection if available
        if self.reflection_system:
            action = f"Generate product recommendations for image: {image_path}, query: {query}"
            context = {"image_path": image_path, "query": query}
            reflection = self.reflection_system.reflect(action, recommendations, context)
            
            # Add reflection insights to recommendations
            recommendations["reflection"] = reflection
        
        return recommendations
    
    def ask_for_rendering(self, image_path: str, recommendations: Dict[str, Any]) -> str:
        """Ask user if they want to see a rendering of recommended products"""
        # Store the request in memory
        request_id = f"render_{len(self.render_requests)}"
        self.render_requests[request_id] = {
            "image_path": image_path,
            "recommendations": recommendations,
            "status": "pending"
        }
        
        # Create a message asking for confirmation
        message = "I've analyzed your image and have some product recommendations. Would you like me to create a visualization showing how the recommended product would look with your image? (yes/no)"
        
        return message, request_id
    
    def create_product_rendering(self, request_id: str, product_description: str = None) -> Tuple[str, Dict[str, Any]]:
        """Create a rendering of a product on the user's image"""
        if request_id not in self.render_requests:
            return "", {"error": f"Request ID not found: {request_id}"}
        
        request = self.render_requests[request_id]
        image_path = request["image_path"]
        
        if not product_description:
            # Extract product description from recommendations
            recommendations = request["recommendations"]
            if "recommendations" in recommendations:
                product_description = recommendations["recommendations"].split("\n")[0]
            else:
                product_description = "A stylish product that matches the user's image"
        
        # Create the rendering
        rendered_image_path, result = self.image_processor.render_product_on_image(image_path, product_description)
        
        # Update request status
        request["status"] = "completed"
        request["result"] = result
        
        # Store in memory if available
        if self.memory_system:
            self.memory_system.add("product_rendering", result, {"request_id": request_id})
        
        return rendered_image_path, result
    
    def get_rendering_request(self, request_id: str) -> Dict[str, Any]:
        """Get a rendering request by ID"""
        if request_id not in self.render_requests:
            return {"error": f"Request ID not found: {request_id}"}
        
        return self.render_requests[request_id]
