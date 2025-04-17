import os
from typing import List, Dict, Any, Optional, Tuple

class Router:
    """Router for directing user queries to appropriate skills"""
    
    def __init__(self):
        self.skills = {}
        
    def register_skill(self, skill_name: str, skill_handler, keywords: List[str]):
        """Register a skill with the router"""
        self.skills[skill_name] = {
            "handler": skill_handler,
            "keywords": keywords
        }
    
    def route(self, query: str, context: Dict[str, Any]) -> Tuple[str, Any]:
        """Route a query to the appropriate skill"""
        query_lower = query.lower()
        
        # Check for exact skill matches first
        for skill_name, skill_info in self.skills.items():
            if any(keyword in query_lower for keyword in skill_info["keywords"]):
                return skill_name, skill_info["handler"](query, context)
        
        # If no exact match, use a more sophisticated approach
        # Calculate match scores for each skill
        skill_scores = {}
        for skill_name, skill_info in self.skills.items():
            score = sum(1 for keyword in skill_info["keywords"] if keyword in query_lower)
            skill_scores[skill_name] = score
        
        # Find the skill with the highest score
        if skill_scores:
            best_skill = max(skill_scores.items(), key=lambda x: x[1])
            if best_skill[1] > 0:
                skill_name = best_skill[0]
                return skill_name, self.skills[skill_name]["handler"](query, context)
        
        # If no skill matches, return default
        return "default", None
