import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ecommerce_agent.search_order_skill")

class SearchOrderSkill:
    """Skill module for searching and retrieving order information"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.order_database = self._load_order_database()
        logger.info("SearchOrderSkill initialized")
    
    def _load_order_database(self) -> List[Dict[str, Any]]:
        """Load the order database"""
        try:
            # Try to load existing database
            if os.path.exists("order_database.json"):
                with open("order_database.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading order database: {str(e)}")
            return []
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the order search skill"""
        logger.info(f"Executing order search skill with query: {query}")
        
        # Create a plan if planner is available
        plan = None
        task_id = None
        if self.planner_system:
            task_id = f"search_order_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            plan = self.planner_system.create_plan(task_id, f"Search for order: {query}", context)
            logger.debug(f"Created plan with task_id: {task_id}")
        
        # Step 1: Identify order reference
        order_id = self._extract_order_id(query, context)
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 0, "completed", {
                "order_id": order_id
            })
        
        # Step 2: Retrieve order details
        order = self._get_order_by_id(order_id)
        
        if not order:
            error_response = {
                "type": "order_search_error",
                "error": "Order not found",
                "query": query,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.reflection_system:
                action = f"Search for order with ID: {order_id}"
                reflection = self.reflection_system.reflect(action, error_response, context)
                error_response["reflection"] = reflection
            
            if plan and task_id:
                self.planner_system.update_step(task_id, 1, "failed", {
                    "reason": "Order not found"
                })
            
            return error_response
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 1, "completed", {
                "order_found": True,
                "order_date": order.get("date_created")
            })
        
        # Step 3: Check order status
        status_info = self._check_order_status(order)
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 2, "completed", {
                "status": status_info["status"],
                "status_details": status_info["details"]
            })
        
        # Prepare response
        response = {
            "type": "order_details",
            "query": query,
            "order": {
                "order_id": order["order_id"],
                "date": order.get("date_created"),
                "product": {
                    "id": order["product_id"],
                    "name": order["product_name"],
                    "price": order["price_per_unit"]
                },
                "quantity": order["quantity"],
                "shipping": order["shipping_info"],
                "payment": {
                    "method": order["payment_info"]["method"],
                    "last4": order["payment_info"].get("last4", "****")
                },
                "total": order["order_details"]["total"],
                "status": status_info["status"],
                "status_details": status_info["details"],
                "estimated_delivery": status_info.get("estimated_delivery")
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to memory if available
        if self.memory_system:
            memory_entry = self.memory_system.add("order_search", response, {
                "query": query,
                "context": context
            })
            response["memory_id"] = memory_entry.get("id")
        
        # Perform self-reflection if available
        if self.reflection_system:
            action = f"Search for order: {order_id}"
            reflection = self.reflection_system.reflect(action, response, context)
            response["reflection"] = reflection
        
        # Complete final step in plan
        if plan and task_id:
            self.planner_system.update_step(task_id, 3, "completed", {
                "response_prepared": True
            })
            response["plan"] = plan
        
        logger.info(f"Order search completed for order_id: {order_id}")
        return response
    
    def _extract_order_id(self, query: str, context: Dict[str, Any]) -> str:
        """Extract order ID from query or context"""
        # Check if order_id is directly provided in context
        if "order_id" in context:
            return context["order_id"]
        
        # Extract order ID from query if present
        import re
        order_id_match = re.search(r"(?:order|#)\s*([A-Za-z]+-\d+)", query, re.IGNORECASE)
        if order_id_match:
            return order_id_match.group(1)
        
        # Look for just the pattern ORD-XXXX
        order_pattern_match = re.search(r"([A-Za-z]+-\d+)", query)
        if order_pattern_match:
            return order_pattern_match.group(1)
        
        # If no order ID found in query, check recent orders in memory
        if self.memory_system:
            recent_orders = self.memory_system.get_by_type("order_confirmation")
            if recent_orders:
                # Return the most recent order ID
                for entry in reversed(recent_orders):
                    if "content" in entry and "order_id" in entry["content"]:
                        return entry["content"]["order_id"]
        
        # If no order ID found, return a default
        if self.order_database:
            # Return the most recent order ID
            return self.order_database[-1]["order_id"]
        
        return "ORD-1001"  # Default order ID if no orders exist
    
    def _get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get an order by its ID"""
        for order in self.order_database:
            if order["order_id"] == order_id:
                return order
        return None
    
    def _check_order_status(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Check the status of an order and provide details"""
        status = order.get("status", "unknown")
        
        # Calculate days since order was created
        days_since_order = 0
        if "date_created" in order:
            try:
                order_date = datetime.fromisoformat(order["date_created"])
                current_date = datetime.now()
                days_since_order = (current_date - order_date).days
            except Exception as e:
                logger.error(f"Error calculating days since order: {str(e)}")
        
        # Generate status details based on status and days
        details = ""
        estimated_delivery = None
        
        if status == "confirmed":
            if days_since_order < 1:
                details = "Your order has been confirmed and is being processed."
                estimated_delivery = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + 
                                     datetime.timedelta(days=5)).isoformat()
            else:
                details = "Your order has been confirmed and will be shipped soon."
                estimated_delivery = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + 
                                     datetime.timedelta(days=4)).isoformat()
        
        elif status == "shipped":
            details = f"Your order was shipped {days_since_order} days ago."
            estimated_delivery = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + 
                                 datetime.timedelta(days=max(1, 3 - days_since_order))).isoformat()
        
        elif status == "delivered":
            details = f"Your order was delivered {days_since_order} days ago."
        
        elif status == "cancelled":
            details = "Your order has been cancelled."
            if "cancellation_reason" in order:
                details += f" Reason: {order['cancellation_reason']}"
        
        else:
            details = "Status information is not available for this order."
        
        status_info = {
            "status": status,
            "details": details,
            "days_since_order": days_since_order
        }
        
        if estimated_delivery:
            status_info["estimated_delivery"] = estimated_delivery
        
        return status_info
