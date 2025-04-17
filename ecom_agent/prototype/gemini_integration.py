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
    
    def generate_content(self, contents: Any, model: str = "gemini-2.0-flash", 
                        response_modalities: List[str] = None) -> Dict[str, Any]:
        """Generic method to generate content using Gemini"""
        try:
            config = None
            if response_modalities:
                config = types.GenerateContentConfig(response_modalities=response_modalities)
            
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            result = {"success": True}
            image_path = None
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    result["text"] = part.text
                elif part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    timestamp = int(time.time())
                    if isinstance(contents, list) and len(contents) > 1:
                        # If we're editing an image
                        image_path = f"edited_products/product_edit_{timestamp}.png"
                    else:
                        # If we're generating a new image
                        image_path = f"generated_products/product_{timestamp}.png"
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image.save(image_path)
                    result["image_path"] = image_path
            
            return image_path, result
            
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {str(e)}")
            return None, {
                "success": False,
                "error": str(e)
            }
    
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text using Gemini"""
        _, result = self.generate_content(prompt)
        return result
    
    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze an image using Gemini"""
        image = Image.open(image_path)
        _, result = self.generate_content([image, prompt])
        return result
    
    def generate_image(self, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Generate an image using Gemini"""
        return self.generate_content(
            prompt,
            model="gemini-2.0-flash-exp-image-generation",
            response_modalities=['TEXT', 'IMAGE']
        )
    
    def edit_image(self, image_path: str, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Edit an image using Gemini"""
        image = Image.open(image_path)
        return self.generate_content(
            [prompt, image],
            model="gemini-2.0-flash-exp-image-generation",
            response_modalities=['TEXT', 'IMAGE']
        )
    
    def generate_variations(self, image_path: str, prompt: str, num_variations: int = 3) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        """Generate variations of an image using Gemini"""
        image = Image.open(image_path)
        variations = []
        for _ in range(num_variations):
            result = self.generate_content(
                [prompt, image],
                model="gemini-2.0-flash-exp-image-generation",
                response_modalities=['TEXT', 'IMAGE']
            )
            variations.append(result)
        return variations
    
    def generate_product_image(self, product_description: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Generate a product image using Gemini"""
        return self.generate_image(product_description)
    
    def edit_product_in_image(self, base_image_path: str, product_description: str, edit_instructions: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Edit an image to add/place a product using Gemini"""
        prompt = f"""
        This is a base image. {edit_instructions}
        Product Description: {product_description}
        Please edit the image to show how the product would look in this setting.
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
            """
            
            image_path, variation_result = self.generate_image(variation_prompt)
            if image_path:
                variations.append(image_path)
                result["variations"].append({
                    "path": image_path,
                    "description": variation_result.get("text", f"Variation {i+1}")
                })
        
        return variations, result 