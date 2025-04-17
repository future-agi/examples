import os
import sys
import json
import logging
from typing import Dict, Any, Optional, Tuple
from openai_integration import OpenAIHelper
from gemini_integration import GeminiHelper

from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

tracer = trace.get_tracer(__name__)

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
from product_recommender import ProductRecommender
from search_skill import SearchSkill
from order_skill import OrderSkill
from search_order_skill import SearchOrderSkill
from cancel_order_skill import CancelOrderSkill
from image_generation_skill import ImageGenerationSkill
from image_editing_skill import ImageEditingSkill

class SkillIntegration:
    """Integration of various e-commerce skills with AI capabilities"""
    
    def __init__(self, memory_system=None, reflection_system=None, planner_system=None):
        self.memory_system = memory_system
        self.reflection_system = reflection_system
        self.planner_system = planner_system
        self.openai_helper = OpenAIHelper()
        self.gemini_helper = GeminiHelper()
        
        # Initialize skill instances
        self.search_skill = SearchSkill()
        self.order_skill = OrderSkill(memory_system, reflection_system, planner_system)
        self.search_order_skill = SearchOrderSkill()
        self.cancel_order_skill = CancelOrderSkill()
        self.product_recommender = ProductRecommender(memory_system, reflection_system)
        self.image_generation_skill = ImageGenerationSkill()
        self.image_editing_skill = ImageEditingSkill()
        
        # Define available skills
        self.skills = {
            "search": self.search_skill,
            "place_order": self.order_skill,
            "search_order": self.search_order_skill,
            "cancel_order": self.cancel_order_skill,
            "recommendation": self.product_recommender,
            "image_generation": self.image_generation_skill,
            "image_editing": self.image_editing_skill,
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
                            "enum": ["search", "place_order", "search_order", "cancel_order", "recommendation", "image_generation", "image_editing", "chat"],
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
    
    def _determine_skill(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        with tracer.start_as_current_span("determine_skill", 
            attributes={
                SpanAttributes.INPUT_VALUE: query,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value,
                SpanAttributes.RAW_INPUT: query,
                SpanAttributes.RAW_OUTPUT: "response",
            }) as span:
            """Use OpenAI's function calling to determine which skill to use"""
            try:
                # Prepare the prompt with image context if available
                prompt_parts = [f"User query: {query}"]
                if context.get("image_path"):
                    prompt_parts.append("Context: User has provided an image.")
                prompt = "\n".join(prompt_parts)
                
                logger.info(f"Determining skill for prompt: {prompt}")
                
                # Use OpenAIHelper for function calling
                response = self.openai_helper.function_completion(
                    messages=[{"role": "user", "content": prompt}],
                    tools=[self.skill_determination_tool]
                )
                
                if not response["success"]:
                    logger.warning(f"Function calling failed: {response.get('error')}. Defaulting to chat.")
                    # Default to chat on failure
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))
                    return {"success": True, "skill": "chat", "confidence": 0.5}
                
                tool_calls = response["tool_calls"]
                if not tool_calls:
                    logger.warning("No tool calls returned by function calling. Defaulting to chat.")
                    # Default to chat if no function called
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))
                    return {"success": True, "skill": "chat", "confidence": 0.5}
                
                # Parse the function arguments
                try:
                    args = json.loads(tool_calls[0].function.arguments)
                    llm_skill_name = args.get("skill_name", "chat") # Get LLM's suggestion
                    confidence = args.get("confidence", 0.5)
                except Exception as e:
                    logger.error(f"Error processing function arguments: {e}. Defaulting to chat.")
                    llm_skill_name = "chat"
                    confidence = 0.5

                logger.info(f"LLM determined skill: {llm_skill_name} with confidence: {confidence}")

                # --- Reworked Image Context Logic --- 
                final_skill_name = llm_skill_name # Start with LLM's choice

                if context.get("image_path"):
                    # CASE 1: Explicit request for image generation?
                    if "generate" in query.lower() or "create" in query.lower():
                        if "image" in query.lower() or "picture" in query.lower() or "photo" in query.lower():
                            logger.info("Image present and query requests generation -> Using image_generation skill.")
                            final_skill_name = "image_generation"
                    # CASE 2: Explicit request for image editing?
                    elif "edit" in query.lower() or "modify" in query.lower() or "change" in query.lower():
                        if "image" in query.lower() or "picture" in query.lower() or "photo" in query.lower():
                            logger.info("Image present and query requests editing -> Using image_editing skill.")
                            final_skill_name = "image_editing"
                    # CASE 3: Image present, but NO explicit gen/edit request? 
                    # -> Default to chat (for vision analysis), regardless of LLM's initial text-based thought.
                    elif final_skill_name != "image_generation" and final_skill_name != "image_editing": 
                        logger.info(f"Image present, no explicit gen/edit keywords. Overriding LLM skill '{llm_skill_name}' to chat for vision analysis.")
                        final_skill_name = "chat"
                    # CASE 4: Image present, and LLM *already* suggested gen/edit (but keywords weren't explicit enough for CASE 1/2). 
                    # -> Let's respect LLM in this edge case for now, but log it.
                    else:
                        logger.info(f"Image present. LLM suggested '{llm_skill_name}' without explicit keywords matching. Proceeding with LLM choice.")
                        pass # Keep final_skill_name as llm_skill_name
                
                # --- End Reworked Logic --- 
                
                # Final validation and return
                if final_skill_name not in self.skills:
                    logger.warning(f"Determined skill '{final_skill_name}' not valid. Defaulting to chat.")
                    final_skill_name = "chat"
                
                logger.info(f"Final determined skill: {final_skill_name}")
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": True, "skill": final_skill_name, "confidence": confidence}))
                return {"success": True, "skill": final_skill_name, "confidence": confidence}
                
            except Exception as e:
                logger.error(f"Error in _determine_skill: {e}", exc_info=True)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": False, "error": str(e)}))
                return {"success": True, "skill": "chat", "confidence": 0.5}
    
    def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        with tracer.start_as_current_span("route_query", 
            attributes={
                SpanAttributes.INPUT_VALUE: query,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value,
                SpanAttributes.RAW_INPUT: query,
                SpanAttributes.RAW_OUTPUT: "response",
            }) as span:
            """Route a query to the appropriate skill using AI"""
            try:
                # Determine which skill to use
                skill_determination = self._determine_skill(query, context)
                
                if not skill_determination["success"]:
                    logger.error(f"Skill determination failed: {skill_determination.get('error', 'Unknown error')}")
                    # Fallback to basic chat if skill determination fails
                    skill_name = "chat"
                else:
                    skill_name = skill_determination["skill"]
                    logger.info(f"Routing to skill: {skill_name}")

                # Handle chat responses (potentially with vision)
                if skill_name == "chat":
                    with tracer.start_as_current_span("chat_response", 
                        attributes={
                            SpanAttributes.INPUT_VALUE: query,
                            SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                            "llm.input_messages.0.message.role": "user",
                            "llm.input_messages.0.message.content": query,
                            SpanAttributes.RAW_INPUT: query,
                            SpanAttributes.RAW_OUTPUT: "response",
                        }) as span:
                        image_path = context.get("image_path")
                        
                        if image_path:
                            logger.info(f"Handling chat with image context: {image_path}")
                            # Use vision completion if image is present
                            chat_response = self.openai_helper.vision_completion(
                                image_path=image_path,
                                prompt=query # Send the user's text query as the prompt
                                # We could add system prompt here if vision_completion supported full message list
                                # For now, it seems simpler: just the image and the user's text query.
                            )
                        else:
                            logger.info("Handling chat without image context")
                            # Use standard chat completion if no image
                            chat_response = self.openai_helper.chat_completion(
                                messages=[
                                    {"role": "system", "content": "You are a helpful e-commerce assistant. Respond naturally to the user's message while maintaining a friendly and professional tone."},
                                    # Pass the current query along with conversation history potentially?
                                    # Let's just pass the current query for now for simplicity.
                                    {"role": "user", "content": query}
                                ]
                            )
                        
                        if not chat_response["success"]:
                            logger.error(f"Chat/Vision completion failed: {chat_response.get('error')}")

                            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(chat_response.get("error", "Unknown chat completion error")))
                            span.set_attribute("llm.output_messages.0.message.role", "assistant")
                            span.set_attribute("llm.output_messages.0.message.content", json.dumps(chat_response.get("error", "Unknown chat completion error")))

                            return {
                                "type": "chat_error",
                                "error": chat_response.get("error", "Unknown chat completion error")
                            }
                        
                        logger.info(f"Chat/Vision response generated successfully.")

                        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(chat_response["content"]))
                        span.set_attribute("llm.output_messages.0.message.role", "assistant")
                        span.set_attribute("llm.output_messages.0.message.content", json.dumps(chat_response["content"]))

                        return {
                            "type": "chat_response",
                            "response": chat_response["content"]
                        }
                
                with tracer.start_as_current_span("execute_skill", 
                    attributes={
                        SpanAttributes.INPUT_VALUE: query,
                        SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                        SpanAttributes.RAW_INPUT: query,
                        SpanAttributes.RAW_OUTPUT: "response",
                    }) as span:

                    # Execute other skills
                    logger.info(f"Executing skill: {skill_name}")
                    skill_instance = self.skills.get(skill_name)
                    if not skill_instance:
                        logger.error(f"Skill instance for '{skill_name}' not found. Defaulting to error.")

                        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"type": "error", "error": f"Skill '{skill_name}' implementation not found."}))

                        return {"type": "error", "error": f"Skill '{skill_name}' implementation not found."}

                    result = skill_instance.execute(query, context)
                    logger.info(f"Skill '{skill_name}' executed.")

                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))

                    return result
                
            except Exception as e:
                logger.error(f"Error routing query: {e}", exc_info=True)
                return {
                    "type": "error",
                    "error": f"An unexpected error occurred during query routing: {str(e)}"
                }
