import os
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
from PIL import Image
import openai
from dotenv import load_dotenv
from gemini_integration import GeminiHelper

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ecommerce_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ecommerce_agent.image_processor")

class ImageProcessor:
    """Handles image processing and product visualization"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.gemini_helper = GeminiHelper()
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image using OpenAI's vision capabilities"""
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this image and describe what you see. Focus on identifying products, styles, colors, and any relevant details for e-commerce purposes."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Extract and return analysis
            analysis = {
                "description": response.choices[0].message.content,
                "detected_objects": self._extract_objects(response.choices[0].message.content),
                "timestamp": response.created
            }
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_objects(self, description: str) -> List[str]:
        """Extract detected objects from the description"""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        objects = []
        
        # Look for common product categories
        categories = ["shirt", "dress", "pants", "shoes", "hat", "jacket", "watch", 
                     "bag", "furniture", "electronics", "phone", "laptop", "camera"]
        
        for category in categories:
            if category in description.lower():
                objects.append(category)
        
        return objects
    
    def generate_product_recommendation(self, image_path: str, user_query: str = "") -> Dict[str, Any]:
        """Generate product recommendations based on an image"""
        try:
            # First analyze the image
            analysis = self.analyze_image(image_path)
            
            # Prepare prompt for recommendation
            prompt = f"Based on the image analysis: {analysis['description']}\n"
            if user_query:
                prompt += f"And considering the user's query: {user_query}\n"
            prompt += "Recommend suitable products for this user."
            
            # Call OpenAI API for recommendations
            response = openai.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a helpful e-commerce assistant that provides product recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            # Extract and return recommendations
            recommendations = {
                "recommendations": response.choices[0].message.content,
                "based_on_image": True,
                "detected_objects": analysis.get("detected_objects", []),
                "timestamp": response.created
            }
            
            return recommendations
            
        except Exception as e:
            return {"error": str(e)}
    
    def render_product_on_image(self, image_path: str, product_description: str) -> Tuple[str, Dict[str, Any]]:
        """Create a rendered image with the recommended product on the user's image using Gemini"""
        try:
            # Read the image file
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            # Create a prompt for Gemini
            prompt = f"""
            Edit this image to include the following product: {product_description}
            Make the product look natural and well-integrated into the scene.
            Maintain the original image's style and lighting.
            """
            
            # Call Gemini to edit the image
            response = self.gemini_helper.edit_image(
                image_data=image_data,
                prompt=prompt
            )
            
            if not response["success"]:
                return "", {"error": response["error"]}
            
            # Save the generated image
            output_path = f"rendered_products/product_render_{int(response['timestamp'])}.png"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as handler:
                handler.write(response["image_data"])
            
            result = {
                "original_image": image_path,
                "product_description": product_description,
                "rendered_image_path": output_path,
                "timestamp": response["timestamp"]
            }
            
            return output_path, result
            
        except Exception as e:
            logger.error(f"Error rendering product on image: {str(e)}")
            return "", {"error": str(e)}
    
    def generate_product_variations(self, image_path: str, product_description: str, num_variations: int = 3) -> Dict[str, Any]:
        """Generate variations of a product using Gemini"""
        try:
            # Read the image file
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            # Create a prompt for Gemini
            prompt = f"""
            Generate {num_variations} variations of this product: {product_description}
            Each variation should show the product in a different style or context.
            Make each variation look realistic and appealing.
            """
            
            # Call Gemini to generate variations
            response = self.gemini_helper.generate_variations(
                image_data=image_data,
                prompt=prompt,
                num_variations=num_variations
            )
            
            if not response["success"]:
                return {"error": response["error"]}
            
            # Save the generated variations
            variations = []
            for i, variation_data in enumerate(response["variations"]):
                output_path = f"rendered_products/product_variation_{i}_{int(response['timestamp'])}.png"
                with open(output_path, 'wb') as handler:
                    handler.write(variation_data)
                variations.append(output_path)
            
            result = {
                "original_image": image_path,
                "product_description": product_description,
                "variations": variations,
                "timestamp": response["timestamp"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating product variations: {str(e)}")
            return {"error": str(e)}
