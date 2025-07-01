import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai_integration import OpenAIHelper
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("ecommerce_agent.search_skill")

class SearchSkill:
    """Skill module for product search functionality"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.product_database = self._load_product_database()
        self.openai_helper = OpenAIHelper()
        logger.info("SearchSkill initialized")
    
    def _load_product_database(self) -> List[Dict[str, Any]]:
        """Load or create a simulated product database"""
        try:
            # Try to load existing database from multiple locations
            for db_path in ["product_database.json", "ecom_agent/observe/product_database.json", "ecom_agent/prototype/product_database.json"]:
                if os.path.exists(db_path):
                    with open(db_path, "r") as f:
                        data = json.load(f)
                        logger.info(f"Loaded product database from {db_path}")
                        return data
        except Exception as e:
            logger.error(f"Error loading product database: {str(e)}")
        
        # Create a simulated database if loading fails
        products = [
            {
                "id": 1,
                "name": "Blue Cotton T-Shirt",
                "category": "clothing",
                "subcategory": "t-shirts",
                "price": 19.99,
                "rating": 4.5,
                "colors": ["blue", "navy", "light blue"],
                "sizes": ["S", "M", "L", "XL"],
                "description": "Comfortable cotton t-shirt in various shades of blue",
                "in_stock": True,
                "stock_count": 150
            },
            {
                "id": 2,
                "name": "Black Leather Jacket",
                "category": "clothing",
                "subcategory": "jackets",
                "price": 89.99,
                "rating": 4.8,
                "colors": ["black"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "description": "Classic black leather jacket with silver zippers",
                "in_stock": True,
                "stock_count": 75
            },
            {
                "id": 3,
                "name": "Wireless Bluetooth Headphones",
                "category": "electronics",
                "subcategory": "audio",
                "price": 129.99,
                "rating": 4.6,
                "colors": ["black", "white", "silver"],
                "description": "High-quality wireless headphones with noise cancellation",
                "in_stock": True,
                "stock_count": 200
            },
            {
                "id": 4,
                "name": "Smartphone Stand",
                "category": "electronics",
                "subcategory": "accessories",
                "price": 15.99,
                "rating": 4.3,
                "colors": ["black", "silver", "rose gold"],
                "description": "Adjustable stand for smartphones and tablets",
                "in_stock": True,
                "stock_count": 300
            },
            {
                "id": 5,
                "name": "Running Shoes",
                "category": "footwear",
                "subcategory": "athletic",
                "price": 79.99,
                "rating": 4.7,
                "colors": ["black/white", "blue/gray", "red/black"],
                "sizes": ["7", "8", "9", "10", "11", "12"],
                "description": "Lightweight running shoes with cushioned soles",
                "in_stock": True,
                "stock_count": 120
            },
            {
                "id": 6,
                "name": "Leather Wallet",
                "category": "accessories",
                "subcategory": "wallets",
                "price": 39.99,
                "rating": 4.4,
                "colors": ["brown", "black"],
                "description": "Genuine leather wallet with multiple card slots",
                "in_stock": True,
                "stock_count": 85
            },
            {
                "id": 7,
                "name": "Coffee Maker",
                "category": "home",
                "subcategory": "kitchen",
                "price": 59.99,
                "rating": 4.2,
                "colors": ["black", "silver", "white"],
                "description": "Programmable coffee maker with 12-cup capacity",
                "in_stock": True,
                "stock_count": 60
            },
            {
                "id": 8,
                "name": "Yoga Mat",
                "category": "fitness",
                "subcategory": "yoga",
                "price": 29.99,
                "rating": 4.5,
                "colors": ["purple", "blue", "green", "black"],
                "description": "Non-slip yoga mat with carrying strap",
                "in_stock": True,
                "stock_count": 100
            },
            {
                "id": 9,
                "name": "Stainless Steel Water Bottle",
                "category": "home",
                "subcategory": "drinkware",
                "price": 24.99,
                "rating": 4.6,
                "colors": ["silver", "black", "blue", "red"],
                "description": "Insulated water bottle that keeps drinks cold for 24 hours",
                "in_stock": True,
                "stock_count": 150
            },
            {
                "id": 10,
                "name": "Wireless Charging Pad",
                "category": "electronics",
                "subcategory": "chargers",
                "price": 34.99,
                "rating": 4.4,
                "colors": ["black", "white"],
                "description": "Fast wireless charging pad compatible with most smartphones",
                "in_stock": True,
                "stock_count": 90
            }
        ]
        
        # Save the database for future use
        try:
            with open("product_database.json", "w") as f:
                json.dump(products, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving product database: {str(e)}")
        
        return products
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search: Analyze image -> Identify relevant categories via LLM -> 
           IF categories found: Return all products in those categories.
           ELSE: Fallback to term/filter search across all categories.
        """
        logger.info(f"Executing search skill with query: '{query}'")
        image_path = context.get("image_path")
        image_analysis_content = None
        # Reset planner variables for clarity
        plan = None 
        task_id = None

        # Optional Image Analysis
        if image_path:
            logger.info(f"Image provided ({image_path}), analyzing for search context...")
            analysis_prompt = f"Describe the searchable attributes (product type, color, style, material, etc.) visible in this image. User query for context: {query}"
            analysis_result = self.openai_helper.vision_completion(image_path, analysis_prompt)
            if analysis_result["success"]:
                image_analysis_content = analysis_result["content"]
                logger.info(f"Image analysis successful: {image_analysis_content[:100]}...")
            else:
                logger.error(f"Image analysis failed: {analysis_result['error']}")

        # --- Category Identification --- 
        # Step 1: Get Unique Categories from DB
        all_categories = sorted(list(set(p['category'] for p in self.product_database if 'category' in p)))
        logger.debug(f"Available categories: {all_categories}")

        # Step 2: LLM identifies relevant categories
        category_prompt_messages = [
            {"role": "system", "content": f"You are an expert category filter. Given a user query, optional image analysis, and a list of available categories, identify which categories are relevant. Respond ONLY with a JSON list of relevant category names (e.g., [\"clothing\", \"electronics\"]). If none seem relevant, return an empty list."}, 
            {"role": "user", "content": f"User Query: {query}\nImage Analysis: {image_analysis_content or 'N/A'}\nAvailable Categories: {json.dumps(all_categories)}"}        
        ]
        logger.info("Identifying relevant categories using LLM.")
        category_result = self.openai_helper.chat_completion(messages=category_prompt_messages, model="gpt-4.1")
        relevant_categories = []
        if category_result["success"]:
            try:
                parsed_categories = json.loads(category_result["content"])
                if isinstance(parsed_categories, list):
                    relevant_categories = [cat for cat in parsed_categories if cat in all_categories]
                    logger.info(f"LLM identified relevant categories: {relevant_categories}")
                else: logger.warning("LLM category response was not a list.")
            except json.JSONDecodeError: logger.error(f"Failed to parse category JSON: {category_result['content']}")
        else: logger.error(f"Category identification failed: {category_result['error']}")
        
        # --- Conditional Execution Path --- 
        search_terms = []
        filters = {}
        
        if relevant_categories:
            # Path 1: Categories identified - Return all products in these categories
            logger.info(f"Relevant categories found ({relevant_categories}). Executing category-only search.")
            ranked_results = self._get_products_by_categories(relevant_categories)
            logger.info(f"Found {len(ranked_results)} products in categories: {relevant_categories}")
            # search_terms and filters remain empty for this path
        else:
            # Path 2: No relevant categories - Fallback to term/filter search
            logger.info("No relevant categories identified by LLM. Falling back to term/filter search.")
            # Step 3 (Fallback): Parse search terms & filters
            search_terms, filters = self._parse_search_query(query, image_analysis_content)
            # Step 4 (Fallback): Execute search across *all* categories
            search_results = self._search_products(search_terms, [], filters) # Pass empty list for categories
            # Step 5 (Fallback): Rank results
            ranked_results = self._rank_results(search_results, context)
            logger.info(f"Fallback search completed with {len(ranked_results)} results.")
        
        # Ensure product images exist for all results
        ranked_results = self.ensure_product_images_exist(ranked_results)
        # --- End Conditional Execution Path --- 

        # Prepare response (consistent structure)
        response = {
            "type": "search_results",
            "query": query,
            "image_analysis": image_analysis_content,
            "search_terms": search_terms, # Will be empty if category path taken
            "relevant_categories": relevant_categories, 
            "filters": filters,         # Will be empty if category path taken
            "results": ranked_results,  # Contains either category results or ranked fallback results
            "total_results": len(ranked_results),
            "has_images": True,  # Indicate that results include images
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to memory if available
        if self.memory_system:
            memory_entry = self.memory_system.add("search_results", response, {
                "query": query,
                "context": context
            })
            response["memory_id"] = memory_entry.get("id")
        
        # Perform self-reflection if available
        if self.reflection_system:
            action = f"Search for products with query: {query}"
            reflection = self.reflection_system.reflect(action, response, context)
            response["reflection"] = reflection
        
        # Complete final step in plan
        if plan and task_id:
            self.planner_system.update_step(task_id, 4, "completed", {
                "response_prepared": True
            })
            response["plan"] = plan
        
        logger.info(f"Search skill finished execution.")
        return response

    def _get_products_by_categories(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Retrieve all products belonging to the specified categories, sorted by name."""
        logger.debug(f"Retrieving all products for categories: {categories}")
        results = [
            product for product in self.product_database 
            if product.get('category') in categories
        ]
        results.sort(key=lambda p: p.get('name', '')) # Sort results by name
        return results

    def _parse_search_query(self, query: str, image_analysis: Optional[str] = None) -> tuple:
        """Parse the search query and integrate image analysis to extract terms/filters."""
        query_lower = query.lower()
        filters = {}
        
        # Price filter
        price_patterns = [
            (r"under \$?(\d+)", "max_price"),
            (r"less than \$?(\d+)", "max_price"),
            (r"cheaper than \$?(\d+)", "max_price"),
            (r"over \$?(\d+)", "min_price"),
            (r"more than \$?(\d+)", "min_price"),
            (r"between \$?(\d+) and \$?(\d+)", "price_range")
        ]
        
        import re
        for pattern, filter_type in price_patterns:
            matches = re.search(pattern, query_lower)
            if matches:
                if filter_type == "price_range":
                    filters["min_price"] = float(matches.group(1))
                    filters["max_price"] = float(matches.group(2))
                else:
                    filters[filter_type] = float(matches.group(1))
        
        # Color filter
        colors = ["black", "white", "red", "blue", "green", "yellow", "purple", 
                 "pink", "orange", "brown", "gray", "silver", "gold"]
        for color in colors:
            if color in query_lower:
                if "colors" not in filters:
                    filters["colors"] = []
                if color not in filters["colors"]:
                    filters["colors"].append(color)
        
        # Size filter
        sizes = ["small", "medium", "large", "s", "m", "l", "xl", "xxl"]
        for size in sizes:
            size_pattern = r"\b" + size + r"\b"
            if re.search(size_pattern, query_lower):
                if "sizes" not in filters:
                    filters["sizes"] = []
                if size not in filters["sizes"]:
                    filters["sizes"].append(size)
        
        # Rating filter
        rating_patterns = [
            (r"(\d+(\.\d+)?) stars?", "min_rating"),
            (r"rated (\d+(\.\d+)?)\+", "min_rating"),
            (r"rating (\d+(\.\d+)?)\+", "min_rating")
        ]
        
        for pattern, filter_type in rating_patterns:
            matches = re.search(pattern, query_lower)
            if matches:
                filters[filter_type] = float(matches.group(1))
        
        # Extract search terms from query AND image analysis
        combined_text = query_lower
        if image_analysis:
            combined_text += " " + image_analysis.lower()
        
        # Remove filter-related words (crude removal, LLM could do better)
        filter_words = ["under", "less than", "cheaper than", "over", "more than", 
                       "between", "and", "stars", "rated", "rating"]
        search_text = combined_text
        for word in filter_words + colors + sizes:
            search_text = re.sub(r'\b' + re.escape(word) + r'\b', '', search_text)
        
        search_text = re.sub(r'\$?\d+(\.\d+)?', '', search_text)
        search_text = re.sub(r'[^w\s]', '', search_text)
        search_terms = [term.strip() for term in search_text.split() if term.strip() and len(term) > 1]
        
        logger.debug(f"Parsed search terms: {search_terms}, Filters: {filters}")
        return search_terms, filters
    
    def _search_products(self, search_terms: List[str], relevant_categories: List[str], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for products within relevant categories, applying terms and filters."""
        results = []
        search_terms_set = set(search_terms)
        logger.debug(f"Searching within categories: {relevant_categories} for terms: {search_terms_set} with filters: {filters}")

        for product in self.product_database:
            # Category filter first
            if relevant_categories and product.get('category') not in relevant_categories:
                continue # Skip if not in a relevant category
            elif not relevant_categories:
                 # If no categories were identified as relevant, should we search all?
                 # Let's search all for now, but log it.
                 if 'category_unfiltered' not in locals(): # Log only once
                      logger.warning("No relevant categories identified by LLM, searching across all categories.")
                      category_unfiltered = True 
            
            # Apply other filters (Price, Color, Size, Rating)
            filter_match = True
            # Price
            if "min_price" in filters and product["price"] < filters["min_price"]: filter_match = False
            if "max_price" in filters and product["price"] > filters["max_price"]: filter_match = False
            # Color
            if "colors" in filters and "colors" in product:
                if not any(filt_col in prod_col.lower() for filt_col in filters["colors"] for prod_col in product["colors"] ):
                    filter_match = False
            # Size
            if "sizes" in filters and "sizes" in product:
                if not any(filt_size.upper() in product["sizes"] or filt_size.lower() in [s.lower() for s in product["sizes"]] for filt_size in filters["sizes"] ):
                    filter_match = False
            # Rating
            if "min_rating" in filters and product["rating"] < filters["min_rating"]: filter_match = False
            
            if not filter_match:
                continue
            
            # Calculate term match score on remaining products
            product_text = f"{product['name']} {product['description']} {product.get('subcategory', '')}".lower()
            term_matches = sum(1 for term in search_terms_set if term in product_text)
            
            if term_matches > 0:
                product_copy = product.copy()
                product_copy["relevance_score"] = term_matches
                results.append(product_copy)
        
        logger.debug(f"Found {len(results)} products after search and filtering.")
        return results
    
    def _rank_results(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank search results based on relevance and user context"""
        # Get user preferences from context if available
        user_preferences = context.get("user_preferences", {})
        
        for product in results:
            # Start with base relevance score
            score = product["relevance_score"]
            
            # Boost by rating
            score += product["rating"] * 0.5
            
            # Boost by stock availability
            if product.get("in_stock", False):
                score += 0.5
            
            # Apply user preference boosts if available
            preferred_categories = user_preferences.get("preferred_categories", [])
            if product["category"] in preferred_categories:
                score += 1.0
            
            preferred_price_range = user_preferences.get("preferred_price_range", {})
            min_price = preferred_price_range.get("min", 0)
            max_price = preferred_price_range.get("max", float("inf"))
            if min_price <= product["price"] <= max_price:
                score += 0.8
            
            # Update the score
            product["ranking_score"] = score
        
        # Sort by ranking score
        ranked_results = sorted(results, key=lambda x: x["ranking_score"], reverse=True)
        
        return ranked_results

    def ensure_product_images_exist(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all products have images, generating them if needed."""
        updated_products = []
        
        for product in products:
            # Create a copy to avoid modifying the original
            product_copy = product.copy()
            
            image_path = product_copy.get('image_url')
            if image_path and os.path.exists(image_path):
                logger.debug(f"Image exists for product {product_copy['id']}: {image_path}")
            else:
                logger.info(f"Generating image for product {product_copy['id']}: {product_copy['name']}")
                generated_path = self.generate_product_image_dalle(product_copy)
                if generated_path:
                    product_copy['image_url'] = generated_path
                    logger.info(f"Generated image: {generated_path}")
                else:
                    # Fallback to placeholder
                    placeholder_path = self.create_placeholder_image(product_copy)
                    product_copy['image_url'] = placeholder_path
                    logger.warning(f"Using placeholder image: {placeholder_path}")
            
            updated_products.append(product_copy)
        
        return updated_products

    def generate_product_image_dalle(self, product: Dict[str, Any]) -> Optional[str]:
        """Generate a product image using DALL-E 3."""
        try:
            # Create category-specific prompts
            category_prompts = {
                "clothing": "Professional product photography of {name} on white background, studio lighting, high quality, commercial photography style",
                "electronics": "Clean product shot of {name} on white background, modern minimalist style, studio lighting, professional photography",
                "footwear": "Professional shoe photography of {name} on white background, side angle, studio lighting, commercial quality",
                "accessories": "Elegant product photography of {name} on white background, luxury style, professional lighting",
                "home": "Clean lifestyle product shot of {name} on white background, modern minimalist style, professional photography",
                "fitness": "Professional product photography of {name} on white background, clean modern style, studio lighting"
            }
            
            category = product.get('category', 'general')
            base_prompt = category_prompts.get(category, "Professional product photography of {name} on white background, studio lighting, high quality")
            
            # Create detailed prompt
            prompt = base_prompt.format(name=product['name'])
            if 'description' in product:
                prompt += f", {product['description']}"
            
            # Create output directory
            os.makedirs("generated_products", exist_ok=True)
            
            # Generate filename
            safe_name = "".join(c for c in product['name'].lower() if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_path = f"generated_products/{safe_name}.png"
            
            # Skip if already exists
            if os.path.exists(output_path):
                logger.info(f"Image already exists: {output_path}")
                return output_path
            
            # Generate image using DALL-E
            logger.info(f"Generating image with DALL-E for: {product['name']}")
            result = self.openai_helper.generate_image(prompt, output_path)
            
            if result.get('success'):
                logger.info(f"Successfully generated image: {output_path}")
                return output_path
            else:
                logger.error(f"DALL-E generation failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating product image: {str(e)}")
            return None

    def create_placeholder_image(self, product: Dict[str, Any]) -> str:
        """Create a placeholder image for the product."""
        try:
            # Create output directory
            os.makedirs("generated_products", exist_ok=True)
            
            # Generate filename
            safe_name = "".join(c for c in product['name'].lower() if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_path = f"generated_products/{safe_name}_placeholder.png"
            
            # Skip if already exists
            if os.path.exists(output_path):
                return output_path
            
            # Create placeholder image
            img = Image.new('RGB', (400, 400), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Add text
            text = product['name']
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (400 - text_width) // 2
            y = (400 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Add price
            price_text = f"${product['price']}"
            price_bbox = draw.textbbox((0, 0), price_text, font=font)
            price_width = price_bbox[2] - price_bbox[0]
            price_x = (400 - price_width) // 2
            price_y = y + text_height + 20
            
            draw.text((price_x, price_y), price_text, fill='darkgreen', font=font)
            
            img.save(output_path)
            logger.info(f"Created placeholder image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {str(e)}")
            return None
