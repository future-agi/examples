import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ecommerce_agent.order_skill")

class OrderSkill:
    """Skill module for placing orders"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.product_database = self._load_product_database()
        self.order_database = self._load_order_database()
        logger.info("OrderSkill initialized")
    
    def _load_product_database(self) -> List[Dict[str, Any]]:
        """Load the product database"""
        try:
            # Try to load existing database
            if os.path.exists("ecom_agent/prototype/product_database.json"):
                with open("ecom_agent/prototype/product_database.json", "r") as f:
                    return json.load(f)
            
            # Create a default product database if it doesn't exist
            default_products = [
                {
                    "id": 1,
                    "name": "Smartphone X",
                    "price": 999.99,
                    "in_stock": True,
                    "stock_count": 50,
                    "description": "Latest smartphone with advanced features"
                },
                {
                    "id": 2,
                    "name": "Laptop Pro",
                    "price": 1499.99,
                    "in_stock": True,
                    "stock_count": 30,
                    "description": "High-performance laptop for professionals"
                },
                {
                    "id": 3,
                    "name": "Wireless Headphones",
                    "price": 199.99,
                    "in_stock": True,
                    "stock_count": 100,
                    "description": "Premium wireless headphones with noise cancellation"
                }
            ]
            
            with open("ecom_agent/prototype/product_database.json", "w") as f:
                json.dump(default_products, f, indent=2)
            
            logger.info("Created default product database")
            return default_products
            
        except Exception as e:
            logger.error(f"Error loading product database: {str(e)}")
            return []
    
    def _load_order_database(self) -> List[Dict[str, Any]]:
        """Load or create the order database"""
        try:
            # Try to load existing database
            if os.path.exists("order_database.json"):
                with open("order_database.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading order database: {str(e)}")
        
        # Create an empty database if loading fails
        orders = []
        
        # Save the database for future use
        try:
            with open("order_database.json", "w") as f:
                json.dump(orders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving order database: {str(e)}")
        
        return orders
    
    def _save_order_database(self):
        """Save the order database"""
        try:
            with open("order_database.json", "w") as f:
                json.dump(self.order_database, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving order database: {str(e)}")
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the order placement skill, handling confirmation step."""
        logger.info(f"Executing order placement skill. Query: '{query}'. Context keys: {list(context.keys())}")
        
        # --- Check if this is a confirmation response --- 
        if context.get("user_confirmation") is not None:
            logger.info("Handling order confirmation response.")
            confirmed = str(context.get("user_confirmation")).lower() == 'yes'
            pending_order_context = context.get("pending_order_context")
            
            if not pending_order_context:
                 logger.error("Confirmation response received, but no pending order context found.")
                 return {"type": "order_error", "error": "Missing context for order confirmation."}

            task_id = pending_order_context.get("task_id")
            plan = self.planner_system.get_plan(task_id) if self.planner_system and task_id else None

            if confirmed:
                logger.info("User confirmed order. Processing...")
                # Update Step 4 (Confirm order details) status
                if plan and task_id:
                    self.planner_system.update_step(task_id, 4, "completed", {"user_decision": "confirmed"})
                
                # Retrieve details needed for processing
                product = self._get_product_by_id(pending_order_context["product_id"])
                quantity = pending_order_context["quantity"]
                shipping_info = pending_order_context["shipping_info"]
                payment_info = pending_order_context["payment_info"]
                order_details = pending_order_context["order_details"]
                
                # Step 5/6: Process order & get final confirmation data
                order_id = self._process_order(product, quantity, shipping_info, payment_info, order_details)
                if plan and task_id:
                    self.planner_system.update_step(task_id, 5, "completed", {"order_id": order_id})
                
                # Prepare final confirmation response
                response = {
                    "type": "order_confirmation",
                    "order_id": order_id,
                    "product": {"id": product["id"], "name": product["name"], "price": product["price"]},
                    "quantity": quantity,
                    "shipping": shipping_info,
                    "payment": {"method": payment_info["method"], "last4": payment_info.get("last4", "****")},
                    "order_details": order_details,
                    "status": "confirmed",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update Step 6 (Provide confirmation)
                if plan and task_id:
                    self.planner_system.update_step(task_id, 6, "completed", {"confirmation_sent": True})
                    response["plan"] = plan # Include final plan state
                    
                logger.info(f"Order placed successfully with order_id: {order_id}")
                # Add to memory/reflection if needed (logic omitted for brevity, should be added back)
                return response
            
            else:
                logger.info("User declined order.")
                # Update Step 4 (Confirm order details) status
                if plan and task_id:
                    self.planner_system.update_step(task_id, 4, "cancelled", {"user_decision": "declined"})
                    # Optionally update overall plan status
                    plan["status"] = "cancelled_by_user"
                
                return {
                    "type": "chat_response", # Use chat response type 
                    "response": "Okay, I have cancelled this order placement."
                }
        # --- End confirmation handling --- 

        # --- Standard Execution Flow (First Pass) --- 
        logger.info("Starting new order placement flow.")
        plan = None
        task_id = None
        if self.planner_system:
            task_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            # Ensure description triggers the correct plan steps
            plan_description = f"Place an order based on query: {query}"
            plan = self.planner_system.create_plan(task_id, plan_description, context)
            logger.debug(f"Created plan with task_id: {task_id}, Steps: {[s['description'] for s in plan['steps']]}")
            # Verify plan has expected steps
            if len(plan.get("steps", [])) != 7:
                 logger.warning("Planner did not generate the expected 7 steps for order placement. Generated %s steps.", len(plan.get("steps", [])))
                 # Handle this? Fallback? For now, continue and hope IDs match.

        # Step 1: Identify product (ID 0)
        product_id, quantity = self._identify_product(query, context)
        product = self._get_product_by_id(product_id)
        if not product:
            error_response = {
                "type": "order_error",
                "error": "Product not found",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.reflection_system:
                action = f"Place order with query: {query}"
                reflection = self.reflection_system.reflect(action, error_response, context)
                error_response["reflection"] = reflection
            
            return error_response
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 0, "completed", {
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": quantity
            })
        
        # Step 2: Verify product availability (ID 1)
        available, stock_info = self._verify_availability(product, quantity)
        if not available:
            error_response = {
                "type": "order_error",
                "error": "Product not available in requested quantity",
                "product": product,
                "requested_quantity": quantity,
                "available_quantity": stock_info.get("stock_count", 0),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.reflection_system:
                action = f"Verify availability for product: {product['name']}"
                reflection = self.reflection_system.reflect(action, error_response, context)
                error_response["reflection"] = reflection
            
            if plan and task_id:
                self.planner_system.update_step(task_id, 1, "failed", {
                    "available": False,
                    "reason": "Insufficient stock"
                })
            
            return error_response
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 1, "completed", {
                "available": True,
                "stock_count": stock_info.get("stock_count", 0)
            })
        
        # Step 3: Collect shipping info (ID 2)
        shipping_info = self._get_shipping_info(context)
        if plan and task_id:
            self.planner_system.update_step(task_id, 2, "completed", {
                "shipping_info": shipping_info
            })
        
        # Step 4: Collect payment info (ID 3)
        payment_info = self._get_payment_info(context)
        if plan and task_id:
            self.planner_system.update_step(task_id, 3, "completed", {
                "payment_method": payment_info.get("method")
            })
        
        # Step 5 logic: Calculate order details (Associated with Plan Step 4 - Confirm details)
        order_details = self._calculate_order_details(product, quantity, shipping_info)
        # Don't update plan step 4 here, just calculated needed info

        # --- Return for Confirmation --- 
        logger.info("Order details calculated. Returning for user confirmation.")
        order_summary = {
             "product_name": product["name"],
             "quantity": quantity,
             "total": order_details["total"],
             "currency": order_details.get("currency", "USD")
        }
        confirmation_prompt = f"Okay, I have the {quantity} x {product['name']} ready. The total is ${order_details['total']:.2f} {order_details.get('currency', 'USD')}. Shall I place the order?"
        
        # Bundle necessary info to continue if confirmed
        internal_context = {
            "product_id": product_id,
            "quantity": quantity,
            "shipping_info": shipping_info,
            "payment_info": payment_info,
            "order_details": order_details,
            "task_id": task_id # Pass task_id to continue plan
        }

        return {
            "type": "needs_order_confirmation",
            "order_summary": order_summary,
            "internal_context": internal_context,
            "confirmation_prompt": confirmation_prompt
        }
        # --- End standard flow --- 
    
    def _identify_product(self, query: str, context: Dict[str, Any]) -> tuple:
        """Identify the product to purchase from the query or context"""
        # Check if product_id is directly provided in context
        if "product_id" in context:
            product_id = context["product_id"]
            quantity = context.get("quantity", 1)
            return product_id, quantity
        
        # Extract product ID from query if present
        import re
        product_id_match = re.search(r"product\s+(?:id\s+)?(\d+)", query.lower())
        if product_id_match:
            product_id = int(product_id_match.group(1))
            
            # Extract quantity if present
            quantity_match = re.search(r"(\d+)\s+(?:units?|pieces?|items?)", query.lower())
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            return product_id, quantity
        
        # If no product ID found, try to match product name
        query_terms = query.lower().split()
        best_match = None
        best_match_score = 0
        
        for product in self.product_database:
            product_name = product["name"].lower()
            match_score = sum(1 for term in query_terms if term in product_name)
            
            if match_score > best_match_score:
                best_match = product
                best_match_score = match_score
        
        if best_match and best_match_score > 0:
            # Extract quantity if present
            quantity_match = re.search(r"(\d+)\s+(?:units?|pieces?|items?)", query.lower())
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            return best_match["id"], quantity
        
        # Default to first product if no match found
        return 1, 1
    
    def _get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product by its ID"""
        for product in self.product_database:
            if product["id"] == product_id:
                return product
        return None
    
    def _verify_availability(self, product: Dict[str, Any], quantity: int) -> tuple:
        """Verify if the product is available in the requested quantity"""
        in_stock = product.get("in_stock", False)
        stock_count = product.get("stock_count", 0)
        
        available = in_stock and stock_count >= quantity
        
        stock_info = {
            "in_stock": in_stock,
            "stock_count": stock_count,
            "requested_quantity": quantity,
            "available": available
        }
        
        return available, stock_info
    
    def _get_shipping_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get shipping information from context or use default"""
        # Check if shipping info is in context
        if "shipping_info" in context:
            return context["shipping_info"]
        
        # Use default shipping info
        return {
            "name": "John Doe",
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "USA",
            "method": "Standard Shipping"
        }
    
    def _get_payment_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get payment information from context or use default"""
        # Check if payment info is in context
        if "payment_info" in context:
            return context["payment_info"]
        
        # Use default payment info
        return {
            "method": "Credit Card",
            "card_type": "Visa",
            "last4": "1234",
            "expiry": "12/25"
        }
    
    def _calculate_order_details(self, product: Dict[str, Any], quantity: int, shipping_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate order details including subtotal, tax, shipping, and total"""
        subtotal = product["price"] * quantity
        
        # Calculate shipping cost based on shipping method
        shipping_method = shipping_info.get("method", "Standard Shipping")
        shipping_cost = 5.99  # Default shipping cost
        
        if shipping_method == "Express Shipping":
            shipping_cost = 12.99
        elif shipping_method == "Next Day Delivery":
            shipping_cost = 19.99
        
        # Calculate tax (simplified as 8% of subtotal)
        tax_rate = 0.08
        tax = round(subtotal * tax_rate, 2)
        
        # Calculate total
        total = subtotal + shipping_cost + tax
        
        return {
            "subtotal": subtotal,
            "shipping_cost": shipping_cost,
            "tax": tax,
            "total": total,
            "currency": "USD"
        }
    
    def _process_order(self, product: Dict[str, Any], quantity: int, shipping_info: Dict[str, Any], payment_info: Dict[str, Any], order_details: Dict[str, Any]) -> str:
        """Process the order and return an order ID"""
        # Generate a unique order ID
        order_count = len(self.order_database)
        order_id = f"ORD-{1001 + order_count}"
        
        # Create order record
        order = {
            "order_id": order_id,
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": quantity,
            "price_per_unit": product["price"],
            "shipping_info": shipping_info,
            "payment_info": {
                "method": payment_info["method"],
                "card_type": payment_info.get("card_type"),
                "last4": payment_info.get("last4")
            },
            "order_details": order_details,
            "status": "confirmed",
            "date_created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Add to order database
        self.order_database.append(order)
        self._save_order_database()
        
        # Update product stock (in a real system, this would be a transaction)
        for i, p in enumerate(self.product_database):
            if p["id"] == product["id"]:
                self.product_database[i]["stock_count"] -= quantity
                if self.product_database[i]["stock_count"] <= 0:
                    self.product_database[i]["in_stock"] = False
                break
        
        return order_id
