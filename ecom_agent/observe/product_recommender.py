import os
import json
import logging # Import logging
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from openai_integration import OpenAIHelper
from gemini_integration import GeminiHelper

logger = logging.getLogger("ecommerce_agent.product_recommender") # Setup logger

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
    
    def ensure_product_images_exist(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure that product images exist, generate if missing"""
        os.makedirs("generated_products", exist_ok=True)
        
        for product in products:
            image_path = product.get("image_url", "")
            if image_path and not os.path.exists(image_path):
                logger.info(f"Generating image for product: {product['name']}")
                
                # Generate product image using DALL-E
                generated_path = self.generate_product_image_dalle(product)
                if generated_path:
                    product["image_url"] = generated_path
                    logger.info(f"Generated image saved to: {generated_path}")
                else:
                    # Fallback: create a placeholder image
                    product["image_url"] = self.create_placeholder_image(product)
        
        return products

    def generate_product_image_dalle(self, product: Dict[str, Any]) -> Optional[str]:
        """Generate a product image using DALL-E"""
        try:
            # Create a detailed prompt for the product
            prompt = f"A high-quality product photo of {product['name']}: {product['description']}. "
            prompt += f"Professional e-commerce style, clean white background, well-lit, "
            
            if product.get('colors'):
                color_str = ', '.join(product['colors'][:2])  # Use first 2 colors
                prompt += f"featuring {color_str} color. "
            
            prompt += "Product photography, commercial quality, detailed and sharp."
            
            # Call OpenAI DALL-E
            result = self.openai_helper.generate_image(prompt)
            
            if result["success"]:
                # Save the image
                filename = f"generated_products/{product['name'].lower().replace(' ', '_').replace('-', '_')}.png"
                
                import requests
                response = requests.get(result["image_url"])
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating image for product {product['name']}: {str(e)}")
            return None

    def create_placeholder_image(self, product: Dict[str, Any]) -> str:
        """Create a placeholder image for products"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple placeholder image
            img = Image.new('RGB', (300, 300), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Add product name to the image
            text = product['name']
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (300 - text_width) // 2
            y = (300 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Save placeholder
            filename = f"generated_products/placeholder_{product['id']}.png"
            img.save(filename)
            return filename
            
        except Exception as e:
            logger.error(f"Error creating placeholder for product {product['name']}: {str(e)}")
            return "generated_products/default_placeholder.png"
    
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
        
        logger.info(f"Image analysis completed for: {image_path}")
        return analysis
    
    def generate_recommendations(self, image_path: Optional[str], query: str) -> Dict[str, Any]:
        """Generate product recommendations using a multi-step LLM approach."""
        logger.info(f"Generating recommendations for query: '{query}' with image: {image_path}")
        
        image_analysis_content = None
        if image_path:
            # Step 1: Analyze the image (if provided)
            image_analysis_result = self.analyze_user_image(image_path, query)
            if "error" in image_analysis_result:
                 logger.error(f"Image analysis failed: {image_analysis_result['error']}")
                 # Proceed without image analysis, relying only on text query
            else:
                 image_analysis_content = image_analysis_result.get('analysis')
                 logger.info("Image analysis successful.")
        
        # Step 2: Extract search criteria using LLM
        criteria_prompt_messages = [
            {"role": "system", "content": "You are an expert at extracting product search criteria from user queries and image descriptions. Identify key features, product types, styles, colors, and any constraints mentioned. Respond ONLY with a JSON object containing extracted criteria (e.g., {'type': 't-shirt', 'color': 'blue', 'style': 'casual'})."},
            {"role": "user", "content": f"User Query: {query}\n\nImage Analysis: {image_analysis_content if image_analysis_content else 'No image provided.'}"}        
        ]
        
        logger.info("Extracting search criteria using LLM.")
        criteria_result = self.openai_helper.chat_completion(messages=criteria_prompt_messages, model="gpt-4.1") # Use a capable model
        
        search_criteria = {}
        if criteria_result["success"]:
            try:
                search_criteria = json.loads(criteria_result["content"])
                logger.info(f"Extracted search criteria: {search_criteria}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse search criteria JSON: {e}. Content: {criteria_result['content']}")
                # Fallback: Use raw query terms if parsing fails
                search_criteria = {"keywords": query.lower().split()}
        else:
            logger.error(f"Criteria extraction failed: {criteria_result['error']}")
            # Fallback: Use raw query terms
            search_criteria = {"keywords": query.lower().split()}

        # Step 3: Pre-filter product database locally
        logger.info("Pre-filtering product database locally.")
        candidate_products = self._filter_products(search_criteria)
        logger.info(f"Found {len(candidate_products)} candidates after filtering.")

        if not candidate_products:
             logger.warning("No candidate products found after filtering.")
             # Return a response indicating no matches found based on criteria
             return {"type": "recommendation_result", "recommendations": [], "message": "Sorry, I couldn't find products matching those specific criteria.", "query": query}

        # Step 4: Get final recommendations from LLM based on candidates
        candidate_product_info = [{k: v for k, v in p.items() if k in ['id', 'name', 'description', 'category', 'price', 'colors']} for p in candidate_products[:20]] # Limit candidates sent

        recommendation_prompt_messages = [
            {"role": "system", "content": f"You are a helpful shopping assistant. Given the user query, image analysis (if any), and a list of candidate products, select the top 3 most relevant products. Respond ONLY with a JSON array of the recommended product IDs (e.g., [1, 5, 3])."},
            {"role": "user", "content": f"User Query: {query}\nImage Analysis: {image_analysis_content if image_analysis_content else 'No image provided.'}\n\nCandidate Products:\n{json.dumps(candidate_product_info, indent=2)}"}
        ]

        logger.info("Getting final recommendations from LLM based on candidates.")
        recommendations_result = self.openai_helper.chat_completion(messages=recommendation_prompt_messages, model="gpt-4.1")

        recommended_products = []
        if recommendations_result["success"]:
            try:
                recommended_ids = json.loads(recommendations_result["content"])
                if isinstance(recommended_ids, list):
                     # Retrieve full product details from the original candidates or DB
                     recommended_products = [p for p in candidate_products if p["id"] in recommended_ids]
                     # Ensure the order matches LLM recommendation if possible
                     recommended_products.sort(key=lambda p: recommended_ids.index(p["id"]) if p["id"] in recommended_ids else float('inf'))
                     logger.info(f"LLM recommended product IDs: {recommended_ids}. Matched: {[p['id'] for p in recommended_products]}")
                else:
                     logger.error(f"LLM recommendation is not a list: {recommended_ids}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse final recommendation JSON: {e}. Content: {recommendations_result['content']}")
            except Exception as e:
                 logger.error(f"Error processing LLM recommendations: {e}")
        else:
            logger.error(f"Final recommendation LLM call failed: {recommendations_result['error']}")

        # Fallback if LLM fails or returns bad format: return top filtered candidates
        if not recommended_products:
             logger.warning("LLM recommendation failed or returned no valid IDs. Falling back to top filtered candidates.")
             recommended_products = candidate_products[:3] # Take top 3 from filtered list

        # Step 5: Ensure product images exist
        recommended_products = self.ensure_product_images_exist(recommended_products)

        # Step 6: Prepare and store response
        recommendations_response = {
            "type": "recommendation_result",
            "image_path": image_path,
            "query": query,
            "search_criteria": search_criteria,
            "recommendations": recommended_products,
            "message": "Here are some products you might like:",
            "has_images": True
        }
            
        if self.memory_system:
             self.memory_system.add("product_recommendations", recommendations_response)
            
        logger.info(f"Returning {len(recommended_products)} recommendations with images.")
        return recommendations_response

    def _filter_products(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter products based on extracted criteria (simple keyword matching)."""
        filtered = []
        keywords = set(criteria.get("keywords", []) + [str(v).lower() for k, v in criteria.items() if k != 'keywords' and isinstance(v, str)])
        if criteria.get('type'): keywords.add(str(criteria['type']).lower())
        if criteria.get('style'): keywords.add(str(criteria['style']).lower())
        if criteria.get('color'): keywords.add(str(criteria['color']).lower())
            
        if not keywords:
             logger.warning("No keywords found in criteria for filtering.")
             return self.product_database[:20] # Return some products if no criteria

        logger.debug(f"Filtering with keywords: {keywords}")

        for product in self.product_database:
            product_text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('subcategory', '')}".lower()
            product_colors = [c.lower() for c in product.get('colors', [])]
            
            match_score = 0
            # Check keywords against text fields
            for keyword in keywords:
                 if keyword in product_text:
                      match_score += 1
            
            # Check color criteria specifically
            if criteria.get('color') and criteria['color'].lower() in product_colors:
                 match_score += 2 # Boost for specific color match

            # Add other filter checks here (price, rating, size) if extracted by LLM
            # Example: 
            # if criteria.get('max_price') and product.get('price') > criteria['max_price']: continue
            # if criteria.get('min_rating') and product.get('rating') < criteria['min_rating']: continue

            if match_score > 0:
                 product_copy = product.copy()
                 product_copy['_filter_score'] = match_score
                 filtered.append(product_copy)
                 
        # Sort by score
        filtered.sort(key=lambda x: x['_filter_score'], reverse=True)
        return filtered
    
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
