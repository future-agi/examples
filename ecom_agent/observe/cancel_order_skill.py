import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ecommerce_agent.cancel_order_skill")

class CancelOrderSkill:
    """Skill module for canceling orders"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.order_database = self._load_order_database()
        logger.info("CancelOrderSkill initialized")
    
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
    
    def _save_order_database(self):
        """Save the order database"""
        try:
            with open("order_database.json", "w") as f:
                json.dump(self.order_database, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving order database: {str(e)}")
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the order cancellation skill"""
        logger.info(f"Executing order cancellation skill with query: {query}")
        
        # Create a plan if planner is available
        plan = None
        task_id = None
        if self.planner_system:
            task_id = f"cancel_order_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            plan = self.planner_system.create_plan(task_id, f"Cancel order: {query}", context)
            logger.debug(f"Created plan with task_id: {task_id}")
        
        # Step 1: Identify order to cancel
        order_id, reason = self._extract_order_info(query, context)
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 0, "completed", {
                "order_id": order_id,
                "reason": reason
            })
        
        # Step 2: Verify cancellation eligibility
        order, eligible, eligibility_info = self._verify_cancellation_eligibility(order_id)
        
        if not order:
            error_response = {
                "type": "cancellation_error",
                "error": "Order not found",
                "query": query,
                "order_id": order_id,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.reflection_system:
                action = f"Cancel order with ID: {order_id}"
                reflection = self.reflection_system.reflect(action, error_response, context)
                error_response["reflection"] = reflection
            
            if plan and task_id:
                self.planner_system.update_step(task_id, 1, "failed", {
                    "reason": "Order not found"
                })
            
            return error_response
        
        if not eligible:
            error_response = {
                "type": "cancellation_error",
                "error": "Order not eligible for cancellation",
                "query": query,
                "order_id": order_id,
                "reason": eligibility_info["reason"],
                "timestamp": datetime.now().isoformat()
            }
            
            if self.reflection_system:
                action = f"Verify cancellation eligibility for order: {order_id}"
                reflection = self.reflection_system.reflect(action, error_response, context)
                error_response["reflection"] = reflection
            
            if plan and task_id:
                self.planner_system.update_step(task_id, 1, "failed", {
                    "eligible": False,
                    "reason": eligibility_info["reason"]
                })
            
            return error_response
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 1, "completed", {
                "eligible": True,
                "reason": eligibility_info["reason"]
            })
        
        # Step 3: Process cancellation
        cancellation_id, refund_info = self._process_cancellation(order, reason)
        
        if plan and task_id:
            self.planner_system.update_step(task_id, 2, "completed", {
                "cancellation_id": cancellation_id,
                "refund_amount": refund_info["amount"]
            })
        
        # Prepare response
        response = {
            "type": "order_cancellation",
            "query": query,
            "order_id": order_id,
            "cancellation_id": cancellation_id,
            "status": "cancelled",
            "reason": reason,
            "refund_amount": refund_info["amount"],
            "refund_method": refund_info["method"],
            "refund_status": refund_info["status"],
            "estimated_refund_date": refund_info["estimated_date"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to memory if available
        if self.memory_system:
            memory_entry = self.memory_system.add("order_cancellation", response, {
                "query": query,
                "context": context
            })
            response["memory_id"] = memory_entry.get("id")
        
        # Perform self-reflection if available
        if self.reflection_system:
            action = f"Cancel order: {order_id}"
            reflection = self.reflection_system.reflect(action, response, context)
            response["reflection"] = reflection
        
        # Complete final step in plan
        if plan and task_id:
            self.planner_system.update_step(task_id, 3, "completed", {
                "confirmation_sent": True
            })
            response["plan"] = plan
        
        logger.info(f"Order cancellation completed for order_id: {order_id}")
        return response
    
    def _extract_order_info(self, query: str, context: Dict[str, Any]) -> tuple:
        """Extract order ID and cancellation reason from query or context"""
        # Check if order_id is directly provided in context
        order_id = context.get("order_id", None)
        reason = context.get("cancellation_reason", "Customer requested cancellation")
        
        if not order_id:
            # Extract order ID from query if present
            import re
            order_id_match = re.search(r"(?:order|#)\s*([A-Za-z]+-\d+)", query, re.IGNORECASE)
            if order_id_match:
                order_id = order_id_match.group(1)
            else:
                # Look for just the pattern ORD-XXXX
                order_pattern_match = re.search(r"([A-Za-z]+-\d+)", query)
                if order_pattern_match:
                    order_id = order_pattern_match.group(1)
        
        # If still no order ID found, check recent orders in memory
        if not order_id and self.memory_system:
            recent_orders = self.memory_system.get_by_type("order_confirmation")
            if recent_orders:
                # Return the most recent order ID
                for entry in reversed(recent_orders):
                    if "content" in entry and "order_id" in entry["content"]:
                        order_id = entry["content"]["order_id"]
                        break
        
        # If still no order ID found, use a default
        if not order_id and self.order_database:
            # Return the most recent order ID
            order_id = self.order_database[-1]["order_id"]
        elif not order_id:
            order_id = "ORD-1001"  # Default order ID if no orders exist
        
        # Extract reason if provided in query
        reason_match = re.search(r"(?:because|reason|due to)\s+(.+?)(?:\.|$)", query, re.IGNORECASE)
        if reason_match:
            reason = reason_match.group(1).strip()
        
        return order_id, reason
    
    def _get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get an order by its ID"""
        for i, order in enumerate(self.order_database):
            if order["order_id"] == order_id:
                return order, i
        return None, -1
    
    def _verify_cancellation_eligibility(self, order_id: str) -> tuple:
        """Verify if an order is eligible for cancellation"""
        order, index = self._get_order_by_id(order_id)
        
        if not order:
            return None, False, {"reason": "Order not found"}
        
        # Check if order is already cancelled
        if order.get("status") == "cancelled":
            return order, False, {"reason": "Order is already cancelled"}
        
        # Check if order is already delivered
        if order.get("status") == "delivered":
            return order, False, {"reason": "Order has already been delivered"}
        
        # Calculate days since order was created
        days_since_order = 0
        if "date_created" in order:
            try:
                order_date = datetime.fromisoformat(order["date_created"])
                current_date = datetime.now()
                days_since_order = (current_date - order_date).days
            except Exception as e:
                logger.error(f"Error calculating days since order: {str(e)}")
        
        # Check if order is too old to cancel (e.g., more than 7 days)
        if days_since_order > 7 and order.get("status") == "shipped":
            return order, False, {"reason": "Order was shipped more than 7 days ago"}
        
        # Order is eligible for cancellation
        eligibility_info = {
            "reason": "Order is eligible for cancellation",
            "days_since_order": days_since_order,
            "current_status": order.get("status")
        }
        
        return order, True, eligibility_info
    
    def _process_cancellation(self, order: Dict[str, Any], reason: str) -> tuple:
        """Process the cancellation and return cancellation ID and refund info"""
        # Generate a cancellation ID
        order_id = order["order_id"]
        cancellation_id = f"CAN-{order_id[4:]}"
        
        # Calculate refund amount
        refund_amount = order["order_details"]["total"]
        
        # Determine refund method based on payment method
        payment_method = order["payment_info"]["method"]
        refund_method = payment_method
        
        # Update order status
        for i, o in enumerate(self.order_database):
            if o["order_id"] == order_id:
                self.order_database[i]["status"] = "cancelled"
                self.order_database[i]["cancellation_id"] = cancellation_id
                self.order_database[i]["cancellation_reason"] = reason
                self.order_database[i]["cancellation_date"] = datetime.now().isoformat()
                self.order_database[i]["refund_amount"] = refund_amount
                self.order_database[i]["refund_method"] = refund_method
                self.order_database[i]["last_updated"] = datetime.now().isoformat()
                break
        
        # Save the updated order database
        self._save_order_database()
        
        # Calculate estimated refund date (3-5 business days from now)
        import random
        refund_days = random.randint(3, 5)
        estimated_refund_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + 
                               datetime.timedelta(days=refund_days)).isoformat()
        
        # Prepare refund info
        refund_info = {
            "amount": refund_amount,
            "method": refund_method,
            "status": "processing",
            "estimated_date": estimated_refund_date
        }
        
        return cancellation_id, refund_info
