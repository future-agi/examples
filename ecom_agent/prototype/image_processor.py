import os
import base64
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
from PIL import Image
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class ImageProcessor:
    """Image processing system using OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image using OpenAI's vision capabilities"""
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o",
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
                model="gpt-4o",
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
        """Create a rendered image with the recommended product on the user's image"""
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call OpenAI DALL-E API
            response = openai.images.edit(
                model="dall-e-3",
                image=open(image_path, "rb"),
                prompt=f"Edit this image to include the following product: {product_description}. Make it look natural and well-integrated.",
                n=1,
                size="1024x1024"
            )
            
            # Save the generated image
            image_url = response.data[0].url
            
            # Generate a unique filename
            timestamp = int(response.created)
            output_path = f"rendered_products/product_render_{timestamp}.png"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download and save the image
            import requests
            img_data = requests.get(image_url).content
            with open(output_path, 'wb') as handler:
                handler.write(img_data)
            
            result = {
                "original_image": image_path,
                "product_description": product_description,
                "rendered_image_path": output_path,
                "timestamp": response.created
            }
            
            return output_path, result
            
        except Exception as e:
            return "", {"error": str(e)}
