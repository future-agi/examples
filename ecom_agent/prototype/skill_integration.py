import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ecommerce_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ecommerce_agent.skill_integration")

# Import skill modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from search_skill import SearchSkill
from order_skill import OrderSkill
from search_order_skill import SearchOrderSkill
from cancel_order_skill import CancelOrderSkill

class SkillIntegration:
    """Integration module for all e-commerce skills"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        """Initialize the skill integration with optional supporting systems"""
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        
        # Initialize all skills
        self.search_skill = SearchSkill(memory_system, reflection_system, planner_system)
        self.order_skill = OrderSkill(memory_system, reflection_system, planner_system)
        self.search_order_skill = SearchOrderSkill(memory_system, reflection_system, planner_system)
        self.cancel_order_skill = CancelOrderSkill(memory_system, reflection_system, planner_system)
        
        logger.info("SkillIntegration initialized with all skills")
    
    def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a query to the appropriate skill"""
        logger.info(f"Routing query: {query}")
        
        # Determine which skill to use based on query
        skill_name, confidence = self._determine_skill(query)
        logger.info(f"Selected skill: {skill_name} with confidence: {confidence}")
        
        # Add routing info to context
        context["routing"] = {
            "selected_skill": skill_name,
            "confidence": confidence
        }
        
        # Execute the selected skill
        if skill_name == "search":
            return self.search_skill.execute(query, context)
        elif skill_name == "order":
            return self.order_skill.execute(query, context)
        elif skill_name == "search_order":
            return self.search_order_skill.execute(query, context)
        elif skill_name == "cancel_order":
            return self.cancel_order_skill.execute(query, context)
        else:
            # Default response if no skill matches
            return {
                "type": "error",
                "error": "No matching skill found",
                "query": query
            }
    
    def _determine_skill(self, query: str) -> Tuple[str, float]:
        """Determine which skill to use based on the query"""
        query_lower = query.lower()
        
        # Define keyword patterns for each skill
        skill_patterns = {
            "search": ["search", "find", "look for", "show me", "what", "where can i get"],
            "order": ["buy", "purchase", "place order", "order", "get", "i want to buy", "i need to purchase"],
            "search_order": ["my order", "order status", "track", "where is my order", "find my order", "check order"],
            "cancel_order": ["cancel", "return", "stop order", "don't want", "refund"]
        }
        
        # Calculate match scores for each skill
        scores = {}
        for skill, patterns in skill_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in query_lower:
                    # Add score based on pattern length (longer patterns are more specific)
                    score += len(pattern) / 5
            scores[skill] = score
        
        # Find the skill with the highest score
        best_skill = max(scores.items(), key=lambda x: x[1])
        skill_name = best_skill[0]
        confidence = best_skill[1]
        
        # If confidence is too low, use more sophisticated analysis
        if confidence < 1.0:
            # Check for order ID pattern which strongly indicates order-related skills
            import re
            order_id_match = re.search(r"(?:order|#)\s*([A-Za-z]+-\d+)", query_lower)
            if order_id_match:
                # If cancel keywords are present, use cancel_order skill
                if any(cancel_word in query_lower for cancel_word in ["cancel", "return", "refund"]):
                    return "cancel_order", 2.0
                # Otherwise use search_order skill
                return "search_order", 2.0
            
            # Check for product-specific patterns
            product_patterns = ["shirt", "shoes", "headphones", "watch", "laptop", "phone"]
            if any(pattern in query_lower for pattern in product_patterns):
                # If order keywords are present, use order skill
                if any(order_word in query_lower for order_word in ["buy", "purchase", "order"]):
                    return "order", 1.5
                # Otherwise use search skill
                return "search", 1.5
        
        return skill_name, confidence
