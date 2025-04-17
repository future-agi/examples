import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple
from openai_integration import OpenAIHelper

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
    """Integration of various e-commerce skills with AI capabilities"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.openai_helper = OpenAIHelper()
        
        # Initialize skill instances
        self.search_skill = SearchSkill()
        self.order_skill = OrderSkill()
        self.search_order_skill = SearchOrderSkill()
        self.cancel_order_skill = CancelOrderSkill()
        
        # Define available skills
        self.skills = {
            "search": self.search_skill,
            "place_order": self.order_skill,
            "search_order": self.search_order_skill,
            "cancel_order": self.cancel_order_skill,
            "chat": None  # Chat will be handled directly by the LLM
        }
        
        # Define skill determination function
        self.skill_determination_tool = {
            "type": "function",
            "function": {
                "name": "determine_skill",
                "description": "Determine which e-commerce skill should handle the user's query. Use 'chat' for generic conversations, greetings, or when no specific e-commerce action is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "enum": ["search", "place_order", "search_order", "cancel_order", "chat"],
                            "description": "The name of the skill that should handle the query. Use 'chat' for generic conversations."
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score for the skill determination (0-1)"
                        }
                    },
                    "required": ["skill_name", "confidence"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    
    def _determine_skill(self, query: str) -> Dict[str, Any]:
        """Use OpenAI's function calling to determine which skill to use"""
        try:
            # Use OpenAIHelper for function calling
            response = self.openai_helper.function_completion(
                messages=[{"role": "user", "content": query}],
                tools=[self.skill_determination_tool]
            )
            
            if not response["success"]:
                return {
                    "success": True,
                    "skill": "chat",
                    "confidence": 0.5
                }
            
            tool_calls = response["tool_calls"]
            if not tool_calls:
                return {
                    "success": True,
                    "skill": "chat",
                    "confidence": 0.5
                }
            
            # Parse the function arguments
            import json
            args = json.loads(tool_calls[0].function.arguments)
            skill_name = args["skill_name"]
            confidence = args["confidence"]
            
            if skill_name not in self.skills:
                return {
                    "success": True,
                    "skill": "chat",
                    "confidence": 0.5
                }
            
            return {
                "success": True,
                "skill": skill_name,
                "confidence": confidence
            }
            
        except Exception as e:
            return {
                "success": True,
                "skill": "chat",
                "confidence": 0.5
            }
    
    def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a query to the appropriate skill using AI"""
        try:
            # Determine which skill to use
            skill_determination = self._determine_skill(query)
            
            if not skill_determination["success"]:
                return {
                    "type": "skill_determination_error",
                    "error": f"Failed to determine skill: {skill_determination['error']}"
                }
            
            skill_name = skill_determination["skill"]
            
            # Handle chat responses directly through the LLM
            if skill_name == "chat":
                chat_response = self.openai_helper.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a helpful e-commerce assistant. Respond naturally to the user's message while maintaining a friendly and professional tone."},
                        {"role": "user", "content": query}
                    ]
                )
                
                if not chat_response["success"]:
                    return {
                        "type": "chat_error",
                        "error": chat_response["error"]
                    }
                
                return {
                    "type": "chat_response",
                    "response": chat_response["content"]
                }
            
            # Execute the appropriate skill
            skill_instance = self.skills[skill_name]
            result = skill_instance.execute(query, context)
            
            return result
            
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            }
