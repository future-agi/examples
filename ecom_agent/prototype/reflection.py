import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class Reflection:
    """Self-reflection system for the e-commerce agent"""
    
    def __init__(self):
        self.reflections = []
    
    def reflect(self, action: str, result: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform self-reflection on an action and its result"""
        timestamp = datetime.now().isoformat()
        
        # Analyze the action and result
        success = self._evaluate_success(action, result)
        improvements = self._suggest_improvements(action, result, context)
        
        reflection = {
            "timestamp": timestamp,
            "action": action,
            "success": success,
            "improvements": improvements,
            "context": context
        }
        
        self.reflections.append(reflection)
        return reflection
    
    def _evaluate_success(self, action: str, result: Any) -> bool:
        """Evaluate if an action was successful based on its result"""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated logic
        if result is None:
            return False
        
        if isinstance(result, str) and "error" in result.lower():
            return False
            
        return True
    
    def _suggest_improvements(self, action: str, result: Any, context: Dict[str, Any]) -> List[str]:
        """Suggest improvements based on the action and result"""
        improvements = []
        
        # Check if action is related to search
        if "search" in action.lower():
            if not self._evaluate_success(action, result):
                improvements.append("Refine search query to be more specific")
                improvements.append("Consider using product categories to narrow search")
        
        # Check if action is related to order placement
        elif "order" in action.lower() and "place" in action.lower():
            if not self._evaluate_success(action, result):
                improvements.append("Ensure all required order information is provided")
                improvements.append("Verify product availability before attempting to place order")
        
        # Check if action is related to recommendations
        elif "recommend" in action.lower():
            if not context.get("image"):
                improvements.append("Ask for more specific preferences to improve recommendations")
            else:
                improvements.append("Ensure image analysis is accurate for better product matching")
        
        # Default improvements
        if not improvements:
            improvements.append("Gather more context from user to improve response accuracy")
            improvements.append("Consider alternative approaches if current method is not effective")
        
        return improvements
    
    def get_recent_reflections(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get the most recent reflections"""
        return self.reflections[-count:] if len(self.reflections) >= count else self.reflections
    
    def get_all_reflections(self) -> List[Dict[str, Any]]:
        """Get all reflections"""
        return self.reflections
    
    def summarize_reflections(self) -> str:
        """Summarize all reflections into actionable insights"""
        if not self.reflections:
            return "No reflections available yet."
        
        # Count success and failure
        success_count = sum(1 for r in self.reflections if r["success"])
        failure_count = len(self.reflections) - success_count
        
        # Collect all improvement suggestions
        all_improvements = []
        for r in self.reflections:
            all_improvements.extend(r["improvements"])
        
        # Count frequency of each improvement
        improvement_counts = {}
        for imp in all_improvements:
            if imp in improvement_counts:
                improvement_counts[imp] += 1
            else:
                improvement_counts[imp] = 1
        
        # Sort improvements by frequency
        sorted_improvements = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Generate summary
        summary = f"Reflection Summary:\n"
        summary += f"- Total actions: {len(self.reflections)}\n"
        summary += f"- Successful actions: {success_count}\n"
        summary += f"- Failed actions: {failure_count}\n\n"
        
        summary += "Top improvement suggestions:\n"
        for imp, count in sorted_improvements[:3]:
            summary += f"- {imp} (suggested {count} times)\n"
        
        return summary
