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
        self.image_generation_skill = ImageGenerationSkill()
        self.image_editing_skill = ImageEditingSkill()
        
        # Define available skills
        self.skills = {
            "search": self.search_skill,
            "place_order": self.order_skill,
            "search_order": self.search_order_skill,
            "cancel_order": self.cancel_order_skill,
            "image_generation": self.image_generation_skill,
            "image_editing": self.image_editing_skill,
            "chat": None  # Chat will be handled directly by the LLM
        }
        
        # Define skill determination function
        self.skill_determination_tool = {
            "type": "function",
            "function": {
                "name": "determine_skill",
                "description": "Determine which e-commerce skill should handle the user's query. Use 'chat' for generic conversations, greetings, product recommendations, or when no specific e-commerce action is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "enum": ["search", "place_order", "search_order", "cancel_order", "image_generation", "image_editing", "chat"],
                            "description": "The name of the skill that should handle the query. Use 'chat' for generic conversations and recommendations."
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
            }) as span:
            try:
                # --- Prepare Prompt --- 
                prompt_parts = []
                history = context.get("conversation_history", [])
                if history:
                    prompt_parts.append("Full Conversation History:")
                    for msg in history:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        img_note = " [Image Attached]" if msg.get("image") else ""
                        prompt_parts.append(f"  {role.capitalize()}{img_note}: {content[:150]}{'...' if len(content) > 150 else ''}")
                    prompt_parts.append("-" * 10)
                
                prompt_parts.append(f"Current User Query: {query}")
                if context.get("image_path"):
                    prompt_parts.append("\nIMPORTANT CONTEXT: The user has attached an image *with this current query*. The query likely refers to this image.")
                    prompt_parts.append("Consider skills like 'search' if the query asks to find similar items, or 'chat' for analysis/recommendations based on the image. Use 'image_editing'/'image_generation' if it asks to modify/create.")
                
                prompt = "\n".join(prompt_parts)
                logger.info(f"Determining skill for prompt (using full history):\n{prompt}")
                span.set_attribute("llm.prompt", prompt) # Add full prompt to span

                # --- Function Calling --- 
                response = self.openai_helper.function_completion(
                    messages=[{"role": "user", "content": prompt}], 
                    tools=[self.skill_determination_tool]
                )
                
                if not response["success"]:
                    logger.warning(f"Function calling failed: {response.get('error')}. Defaulting to chat.")
                    # Default to chat on failure
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))
                    span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))

                    return {"success": True, "skill": "chat", "confidence": 0.5}
                
                tool_calls = response["tool_calls"]
                if not tool_calls:
                    logger.warning("No tool calls returned by function calling. Defaulting to chat.")
                    # Default to chat if no function called
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))
                    span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"success": True, "skill": "chat", "confidence": 0.5}))

                    return {"success": True, "skill": "chat", "confidence": 0.5}
                
                # --- Parse Arguments --- 
                try:
                    args = json.loads(tool_calls[0].function.arguments)
                    llm_skill_name = args.get("skill_name", "chat")
                    confidence = args.get("confidence", 0.5)
                    logger.info(f"LLM determined skill: {llm_skill_name} with confidence: {confidence}")
                    span.set_attribute("llm.response", json.dumps(args)) # Log parsed args
                except Exception as e: # Catch JSONDecodeError and others
                    logger.error(f"Error processing function arguments: {e}. Raw args: {tool_calls[0].function.arguments}. Defaulting to chat.")
                    llm_skill_name = "chat"
                    confidence = 0.5
                    span.set_attribute("error.message", f"Argument parsing error: {e}")

                # --- Apply Image Context Logic (Trusting) --- 
                final_skill_name = llm_skill_name
                if context.get("image_path"):
                    if ("generate" in query.lower() or "create" in query.lower()) and \
                       ("image" in query.lower() or "picture" in query.lower() or "photo" in query.lower()):
                        logger.info("Image present and query requests generation -> Using image_generation skill.")
                        final_skill_name = "image_generation"
                    elif ("edit" in query.lower() or "modify" in query.lower() or "change" in query.lower()) and \
                         ("image" in query.lower() or "picture" in query.lower() or "photo" in query.lower()):
                        logger.info("Image present and query requests editing -> Using image_editing skill.")
                        final_skill_name = "image_editing"
                    elif final_skill_name in ["place_order", "cancel_order", "search_order"]:
                        logger.warning(f"Image present, but LLM chose irrelevant skill '{llm_skill_name}'. Overriding to chat for vision analysis.")
                        final_skill_name = "chat"
                    else: 
                        logger.info(f"Image present. Trusting LLM determined skill: '{llm_skill_name}'.")
                
                # --- Final Validation --- 
                if final_skill_name not in self.skills:
                    logger.warning(f"Determined skill '{final_skill_name}' not valid. Defaulting to chat.")
                    final_skill_name = "chat"
                
                logger.info(f"Final determined skill: {final_skill_name}")
                result = {"success": True, "skill": final_skill_name, "confidence": confidence}
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
                
            except Exception as e:
                logger.error(f"Error in _determine_skill: {e}", exc_info=True)
                result = {"success": True, "skill": "chat", "confidence": 0.5} # Default to chat on unexpected error
                span.set_attribute("error.message", str(e))
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
                return result
    
    def route_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        with tracer.start_as_current_span("route_query", 
            attributes={
                SpanAttributes.INPUT_VALUE: query,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value,
                SpanAttributes.RAW_INPUT: query,
                SpanAttributes.RAW_OUTPUT: "response", # Will be updated
            }) as span:
            try:
                skill_determination = self._determine_skill(query, context)
                
                if not skill_determination["success"]:
                    logger.error(f"Skill determination failed: {skill_determination.get('error', 'Unknown error')}")
                    skill_name = "chat"
                else:
                    skill_name = skill_determination["skill"]
                    logger.info(f"Routing to skill: {skill_name}")
                    span.set_attribute("agent.skill", skill_name) # Log chosen skill

                # --- Handle Chat Skill --- 
                if skill_name == "chat":
                    # Wrap the chat LLM call in its own span
                    with tracer.start_as_current_span("chat_response_llm", 
                        attributes={
                            SpanAttributes.INPUT_VALUE: query,
                            SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                            # Add more relevant attributes if needed
                        }) as llm_span:
                        
                        image_path = context.get("image_path")
                        history = context.get("conversation_history", []) # Get history
                        
                        if image_path:
                            logger.info(f"Handling chat with image context: {image_path}. Using OpenAI vision_completion.")
                            llm_span.set_attribute("llm.model_name", "gpt-4.1") # Assuming model
                            llm_span.set_attribute("image.url", image_path) 
                            chat_response = self.openai_helper.vision_completion(
                                image_path=image_path,
                                prompt=query 
                            )
                        else:
                            logger.info("Handling chat without image context using OpenAI. Including full history.")
                            messages_for_llm = []
                            messages_for_llm.append({"role": "system", "content": "You are a helpful e-commerce assistant..."}) 
                            for msg in history[:-1]: 
                                 role = msg.get('role')
                                 content = msg.get('content')
                                 if role and content and not msg.get('image'): 
                                      messages_for_llm.append({"role": role, "content": content})
                            messages_for_llm.append({"role": "user", "content": query})
                            
                            llm_span.set_attribute("llm.model_name", "gpt-4.1") # Assuming model
                            for i, msg in enumerate(messages_for_llm):
                                 llm_span.set_attribute(f"llm.input_messages.{i}.message.role", msg["role"])        
                                 llm_span.set_attribute(f"llm.input_messages.{i}.message.content", msg["content"])

                            chat_response = self.openai_helper.chat_completion(
                                messages=messages_for_llm
                            )
                        
                        # Process response and update span
                        if not chat_response or not chat_response.get("success"):
                            error_msg = chat_response.get("error", "Unknown OpenAI chat error") if chat_response else "Unknown OpenAI chat error"
                            logger.error(f"OpenAI Chat/Vision completion failed: {error_msg}")
                            llm_span.set_attribute("error.message", error_msg)
                            llm_span.set_attribute(SpanAttributes.OUTPUT_VALUE, error_msg)
                            # Adding missing RAW_OUTPUT for error case
                            llm_span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"error": error_msg})) 
                            final_result = {"type": "chat_error", "error": error_msg}
                        else:
                            response_content = chat_response.get("content", "")
                            logger.info("OpenAI Chat/Vision response generated successfully.")
                            llm_span.set_attribute(SpanAttributes.OUTPUT_VALUE, response_content)
                            llm_span.set_attribute("llm.output_messages.0.message.role", "assistant")
                            llm_span.set_attribute("llm.output_messages.0.message.content", response_content)
                            # Adding missing RAW_OUTPUT for success case
                            llm_span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"response": response_content})) 
                            final_result = {"type": "chat_response", "response": response_content}
                            
                    # This block should be OUTSIDE the chat_response_llm span
                    span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))
                    return final_result # Return result from chat skill block

                # --- Handle Other Skills --- 
                # This block should be at the same indentation level as the `if skill_name == "chat":` block
                
                # Check for image before editing (no change needed here)
                if skill_name == "image_editing" and not context.get("image_path"):
                    logger.info("Image editing skill selected, but no image provided...")
                    final_result = {
                         "type": "chat_response", 
                         "response": "It looks like you want to edit an image..."
                    }
                    span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))
                    return final_result

                # Wrap skill execution in its own span
                with tracer.start_as_current_span(f"execute_{skill_name}", 
                    attributes={
                        SpanAttributes.INPUT_VALUE: query,
                        SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value, 
                        SpanAttributes.TOOL_NAME: skill_name,
                        SpanAttributes.RAW_INPUT: query,
                    }) as skill_span:
                    
                    skill_instance = self.skills.get(skill_name)
                    if not skill_instance:
                        logger.error(f"Skill instance for '{skill_name}' not found.")
                        final_result = {"type": "error", "error": f"Skill '{skill_name}' implementation not found."}
                        skill_span.set_attribute("error.message", final_result["error"])
                        skill_span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))
                    else:
                        try:
                            result = skill_instance.execute(query, context)
                            logger.info(f"Skill '{skill_name}' executed.")
                            final_result = result
                            # Safely serialize result for span
                            try:
                                 final_result_json = json.dumps(final_result)
                            except Exception as json_e:
                                 logger.warning(f"Could not serialize skill result for tracing: {json_e}")
                                 final_result_json = "[Serialization Error]"
                            skill_span.set_attribute(SpanAttributes.RAW_OUTPUT, final_result_json)
                        except Exception as skill_e:
                            logger.error(f"Error executing skill '{skill_name}': {skill_e}", exc_info=True)
                            final_result = {"type": "error", "error": f"Error during {skill_name}: {str(skill_e)}"}
                            skill_span.set_attribute("error.message", str(skill_e))
                            skill_span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))

                # This block should be OUTSIDE the skill_execution span
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))
                return final_result
                
            except Exception as e:
                # This block should be aligned with the outer try
                logger.error(f"Error routing query: {e}", exc_info=True)
                final_result = {"type": "error", "error": f"An unexpected error occurred: {str(e)}"}
                span.set_attribute("error.message", str(e))
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(final_result))
                return final_result
