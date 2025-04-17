import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class Planner:
    """Planning system for breaking down complex tasks"""
    
    def __init__(self):
        self.plans = {}
        self.plan_history = []
    
    def create_plan(self, task_id: str, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a plan for a complex task"""
        timestamp = datetime.now().isoformat()
        
        # Generate steps based on task description
        steps = self._generate_steps(task_description, context)
        
        plan = {
            "task_id": task_id,
            "timestamp": timestamp,
            "description": task_description,
            "steps": steps,
            "current_step": 0,
            "completed_steps": [],
            "status": "created",
            "context": context or {}
        }
        
        self.plans[task_id] = plan
        self.plan_history.append({
            "timestamp": timestamp,
            "action": "create",
            "task_id": task_id,
            "description": task_description
        })
        
        return plan
    
    def _generate_steps(self, task_description: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate steps for a task based on its description"""
        steps = []
        
        # Search-related task
        if any(term in task_description.lower() for term in ["search", "find", "look for"]):
            steps = [
                {"id": 0, "description": "Parse search query from user input", "status": "pending"},
                {"id": 1, "description": "Identify product categories and filters", "status": "pending"},
                {"id": 2, "description": "Execute search with parameters", "status": "pending"},
                {"id": 3, "description": "Process and rank search results", "status": "pending"},
                {"id": 4, "description": "Present results to user", "status": "pending"}
            ]
        
        # Order placement task
        elif any(term in task_description.lower() for term in ["place order", "buy", "purchase"]):
            steps = [
                {"id": 0, "description": "Identify product to purchase", "status": "pending"},
                {"id": 1, "description": "Verify product availability", "status": "pending"},
                {"id": 2, "description": "Collect shipping information", "status": "pending"},
                {"id": 3, "description": "Collect payment information", "status": "pending"},
                {"id": 4, "description": "Confirm order details with user", "status": "pending"},
                {"id": 5, "description": "Process order", "status": "pending"},
                {"id": 6, "description": "Provide order confirmation", "status": "pending"}
            ]
        
        # Order search task
        elif any(term in task_description.lower() for term in ["find order", "order status", "track"]):
            steps = [
                {"id": 0, "description": "Identify order reference", "status": "pending"},
                {"id": 1, "description": "Retrieve order details", "status": "pending"},
                {"id": 2, "description": "Check order status", "status": "pending"},
                {"id": 3, "description": "Present order information to user", "status": "pending"}
            ]
        
        # Order cancellation task
        elif any(term in task_description.lower() for term in ["cancel order", "return"]):
            steps = [
                {"id": 0, "description": "Identify order to cancel", "status": "pending"},
                {"id": 1, "description": "Verify cancellation eligibility", "status": "pending"},
                {"id": 2, "description": "Process cancellation request", "status": "pending"},
                {"id": 3, "description": "Confirm cancellation with user", "status": "pending"}
            ]
        
        # Product recommendation task
        elif any(term in task_description.lower() for term in ["recommend", "suggest"]):
            steps = [
                {"id": 0, "description": "Identify user preferences", "status": "pending"},
                {"id": 1, "description": "Process any provided images", "status": "pending"},
                {"id": 2, "description": "Generate product recommendations", "status": "pending"},
                {"id": 3, "description": "Check if user wants image rendering", "status": "pending"},
                {"id": 4, "description": "Create product visualization if requested", "status": "pending"},
                {"id": 5, "description": "Present recommendations to user", "status": "pending"}
            ]
        
        # Default generic task
        else:
            steps = [
                {"id": 0, "description": "Understand user request", "status": "pending"},
                {"id": 1, "description": "Gather necessary information", "status": "pending"},
                {"id": 2, "description": "Process the request", "status": "pending"},
                {"id": 3, "description": "Provide response to user", "status": "pending"}
            ]
        
        return steps
    
    def update_step(self, task_id: str, step_id: int, status: str, result: Any = None) -> Dict[str, Any]:
        """Update the status of a step in a plan"""
        if task_id not in self.plans:
            raise ValueError(f"Task ID {task_id} not found")
        
        plan = self.plans[task_id]
        
        # Find the step with the given ID
        step = next((s for s in plan["steps"] if s["id"] == step_id), None)
        if not step:
            raise ValueError(f"Step ID {step_id} not found in task {task_id}")
        
        # Update the step
        step["status"] = status
        if result:
            step["result"] = result
        
        # Update timestamp
        timestamp = datetime.now().isoformat()
        step["updated_at"] = timestamp
        
        # If step is completed, add to completed steps
        if status == "completed" and step_id not in plan["completed_steps"]:
            plan["completed_steps"].append(step_id)
        
        # Update current step if needed
        if status == "completed" and plan["current_step"] == step_id:
            next_pending = next((s["id"] for s in plan["steps"] if s["status"] == "pending"), None)
            if next_pending is not None:
                plan["current_step"] = next_pending
        
        # Check if all steps are completed
        all_completed = all(s["status"] == "completed" for s in plan["steps"])
        if all_completed:
            plan["status"] = "completed"
        
        # Add to history
        self.plan_history.append({
            "timestamp": timestamp,
            "action": "update_step",
            "task_id": task_id,
            "step_id": step_id,
            "status": status
        })
        
        return plan
    
    def get_plan(self, task_id: str) -> Dict[str, Any]:
        """Get a plan by its task ID"""
        if task_id not in self.plans:
            raise ValueError(f"Task ID {task_id} not found")
        
        return self.plans[task_id]
    
    def get_all_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all plans"""
        return self.plans
    
    def get_plan_history(self) -> List[Dict[str, Any]]:
        """Get the history of plan actions"""
        return self.plan_history
