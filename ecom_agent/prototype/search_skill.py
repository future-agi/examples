import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ecommerce_agent.search_skill")

class SearchSkill:
    """Skill module for product search functionality"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.product_database = self._load_product_database()
        logger.info("SearchSkill initialized")
    
    def _load_product_database(self) -> List[Dict[str, Any]]:
        """Load or create a simulated product database"""
        try:
            # Try to load existing database
            if os.path.exists("product_database.json"):
                with open("product_database.json", "r") as f:
                    return json.load(f)
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
        """Execute the search skill"""
        logger.info(f"Executing search skill with query: {query}")
        
        # Create a plan if planner is available
        plan = None
        task_id = None
        if self.planner_system:
            task_id = f"search_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            plan = self.planner_system.create_plan(task_id, f"Search for products: {query}", context)
            logger.debug(f"Created plan with task_id: {task_id}")
        
        # Step 1: Parse search query
        search_terms, filters = self._parse_search_query(query)
        if plan and task_id:
            self.planner_system.update_step(task_id, 0, "completed", {
                "search_terms": search_terms,
                "filters": filters
            })
        
        # Step 2: Identify product categories and filters
        categories = self._identify_categories(search_terms)
        if plan and task_id:
            self.planner_system.update_step(task_id, 1, "completed", {
                "categories": categories,
                "refined_filters": filters
            })
        
        # Step 3: Execute search
        search_results = self._search_products(search_terms, categories, filters)
        if plan and task_id:
            self.planner_system.update_step(task_id, 2, "completed", {
                "results_count": len(search_results)
            })
        
        # Step 4: Process and rank results
        ranked_results = self._rank_results(search_results, context)
        if plan and task_id:
            self.planner_system.update_step(task_id, 3, "completed", {
                "ranked_results": [p["id"] for p in ranked_results[:5]]
            })
        
        # Prepare response
        response = {
            "type": "search_results",
            "query": query,
            "search_terms": search_terms,
            "categories": categories,
            "filters": filters,
            "results": ranked_results,
            "total_results": len(ranked_results),
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
        
        logger.info(f"Search completed with {len(ranked_results)} results")
        return response
    
    def _parse_search_query(self, query: str) -> tuple:
        """Parse the search query to extract search terms and filters"""
        query_lower = query.lower()
        
        # Extract filters
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
                filters["colors"].append(color)
        
        # Size filter
        sizes = ["small", "medium", "large", "s", "m", "l", "xl", "xxl"]
        for size in sizes:
            size_pattern = r"\b" + size + r"\b"
            if re.search(size_pattern, query_lower):
                if "sizes" not in filters:
                    filters["sizes"] = []
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
        
        # Extract search terms (remove filter-related words)
        filter_words = ["under", "less than", "cheaper than", "over", "more than", 
                       "between", "and", "stars", "rated", "rating"]
        
        search_terms = query_lower
        for word in filter_words:
            search_terms = search_terms.replace(word, "")
        
        # Remove price mentions
        search_terms = re.sub(r"\$?\d+(\.\d+)?", "", search_terms)
        
        # Clean up and split into terms
        search_terms = re.sub(r"[^\w\s]", "", search_terms)
        search_terms = [term.strip() for term in search_terms.split() if term.strip()]
        
        return search_terms, filters
    
    def _identify_categories(self, search_terms: List[str]) -> List[str]:
        """Identify product categories based on search terms"""
        category_keywords = {
            "clothing": ["shirt", "t-shirt", "tshirt", "jacket", "pants", "jeans", "dress", "sweater", "hoodie", "clothes"],
            "electronics": ["phone", "laptop", "computer", "tablet", "headphones", "earbuds", "speaker", "camera", "tv", "television"],
            "footwear": ["shoes", "boots", "sneakers", "sandals", "footwear"],
            "accessories": ["watch", "wallet", "bag", "purse", "backpack", "sunglasses", "hat", "jewelry"],
            "home": ["furniture", "chair", "table", "bed", "sofa", "couch", "lamp", "kitchen", "appliance"],
            "fitness": ["exercise", "workout", "fitness", "yoga", "weights", "gym"]
        }
        
        identified_categories = []
        for term in search_terms:
            for category, keywords in category_keywords.items():
                if term in keywords:
                    identified_categories.append(category)
        
        return list(set(identified_categories))
    
    def _search_products(self, search_terms: List[str], categories: List[str], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for products based on search terms, categories, and filters"""
        results = []
        
        for product in self.product_database:
            # Check if product matches search terms
            product_text = f"{product['name']} {product['description']} {product['category']} {product.get('subcategory', '')}"
            product_text = product_text.lower()
            
            # Calculate term match score
            term_matches = sum(1 for term in search_terms if term in product_text)
            
            # Check category match
            category_match = not categories or product['category'] in categories
            
            # Check filters
            filter_match = True
            
            # Price filters
            if "min_price" in filters and product["price"] < filters["min_price"]:
                filter_match = False
            if "max_price" in filters and product["price"] > filters["max_price"]:
                filter_match = False
            
            # Color filters
            if "colors" in filters and "colors" in product:
                color_match = False
                for color in filters["colors"]:
                    for product_color in product["colors"]:
                        if color in product_color.lower():
                            color_match = True
                            break
                if not color_match:
                    filter_match = False
            
            # Size filters
            if "sizes" in filters and "sizes" in product:
                size_match = False
                for size in filters["sizes"]:
                    if size.upper() in product["sizes"] or size.lower() in [s.lower() for s in product["sizes"]]:
                        size_match = True
                        break
                if not size_match:
                    filter_match = False
            
            # Rating filter
            if "min_rating" in filters and product["rating"] < filters["min_rating"]:
                filter_match = False
            
            # Add to results if matches
            if term_matches > 0 and category_match and filter_match:
                product_copy = product.copy()
                product_copy["relevance_score"] = term_matches
                results.append(product_copy)
        
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
