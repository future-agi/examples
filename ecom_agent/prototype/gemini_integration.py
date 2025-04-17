from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import os
import time
import logging
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ecommerce_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ecommerce_agent.gemini_helper")

class GeminiHelper:
    """Helper class for Gemini API interactions"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Create directories for storing images
        os.makedirs("generated_products", exist_ok=True)
        os.makedirs("edited_products", exist_ok=True)
        logger.info("Created directories for storing generated and edited images")
    
    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze an image using Gemini"""
        try:
            image = Image.open(image_path)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[image, prompt]
            )
            
            if response.text:
                return {
                    "success": True,
                    "analysis": response.text
                }
            return {
                "success": False,
                "error": "No text response received"
            }
        except Exception as e:
            logger.error(f"Error analyzing image with Gemini: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_image(self, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Generate an image using Gemini"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            result = {"success": True}
            image_path = None
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    result["text"] = part.text
                elif part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    timestamp = int(time.time())
                    image_path = f"generated_products/product_{timestamp}.png"
                    image.save(image_path)
                    result["image_path"] = image_path
            
            return image_path, result
            
        except Exception as e:
            logger.error(f"Error generating image with Gemini: {str(e)}")
            return None, {
                "success": False,
                "error": str(e)
            }
    
    def edit_image(self, image_path: str, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Edit an image using Gemini"""
        try:
            image = Image.open(image_path)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            result = {"success": True}
            image_path = None
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    result["text"] = part.text
                elif part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    timestamp = int(time.time())
                    image_path = f"edited_products/product_edit_{timestamp}.png"
                    image.save(image_path)
                    result["image_path"] = image_path
            
            return image_path, result
            
        except Exception as e:
            logger.error(f"Error editing image with Gemini: {str(e)}")
            return None, {
                "success": False,
                "error": str(e)
            }
    
    def generate_product_image(self, product_description: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Generate a product image using Gemini"""
        prompt = f"""
        Create a 3D rendered product image based on this description:
        {product_description}
        The image should be photorealistic and show the product from multiple angles.
        """
        return self.generate_image(prompt)
    
    def edit_product_in_image(self, base_image_path: str, product_description: str, edit_instructions: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Edit an image to add/place a product using Gemini"""
        prompt = f"""
        This is a base image. {edit_instructions}
        Product Description: {product_description}
        Please edit the image to show how the product would look in this setting.
        Make sure the product looks realistic and properly integrated into the scene.
        """
        return self.edit_image(base_image_path, prompt)
    
    def generate_product_variations(self, product_description: str, num_variations: int = 3) -> Tuple[List[str], Dict[str, Any]]:
        """Generate multiple variations of a product image"""
        variations = []
        result = {"success": True, "variations": []}
        
        for i in range(num_variations):
            variation_prompt = f"""
            Generate a variation of this product with different colors/styles:
            {product_description}
            Variation {i+1} should have unique characteristics.
            Make it look realistic and professional.
            """
            
            image_path, variation_result = self.generate_image(variation_prompt)
            if image_path:
                variations.append(image_path)
                result["variations"].append({
                    "path": image_path,
                    "description": variation_result.get("text", f"Variation {i+1}")
                })
        
        return variations, result 