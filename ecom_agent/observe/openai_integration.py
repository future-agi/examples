import os
import base64
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues
import logging

tracer = trace.get_tracer(__name__)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIHelper:
    """Helper class for basic OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI()
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4.1", max_tokens: int = 1000) -> Dict[str, Any]:
        with tracer.start_as_current_span("chat_completion", 
            attributes={
                SpanAttributes.INPUT_VALUE: json.dumps(messages),
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                SpanAttributes.RAW_INPUT: json.dumps(messages),
            }) as span:
            """Basic chat completion with OpenAI"""
            try:
                for i, message in enumerate(messages):
                    if message.get("role") and message.get("content"):
                        span.set_attribute(f"llm.input_messages.{i}.message.role", message["role"])
                        span.set_attribute(f"llm.input_messages.{i}.message.content", message["content"])

                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens
                )
                span.set_attribute("llm.output_messages.0.message.role", "assistant")
                span.set_attribute("llm.output_messages.0.message.content", json.dumps(response.choices[0].message.content))
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response.choices[0].message.content))
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response.choices[0].message.content))
                return {
                    "content": response.choices[0].message.content,
                    "success": True
                }
            except Exception as e:
                span.set_attribute("error.message", str(e))
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(e))
                span.set_attribute(SpanAttributes.RAW_OUTPUT, str(e))
                return {
                    "error": str(e),
                    "success": False
                }
    
    def vision_completion(self, image_path: str, prompt: str, model: str = "gpt-4.1", max_tokens: int = 300) -> Dict[str, Any]:
        with tracer.start_as_current_span("vision_completion", 
            attributes={
                SpanAttributes.INPUT_VALUE: prompt,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                SpanAttributes.RAW_INPUT: prompt,
            }) as span:
            """Basic vision completion with OpenAI"""
            try:
                # Determine image type (basic implementation)
                image_type = "image/jpeg" # Default
                if image_path.lower().endswith(".png"):
                    image_type = "image/png"
                elif image_path.lower().endswith(".jpg") or image_path.lower().endswith(".jpeg"):
                    image_type = "image/jpeg"
                elif image_path.lower().endswith(".gif"):
                    image_type = "image/gif"
                elif image_path.lower().endswith(".webp"):
                    image_type = "image/webp"
                
                with open(image_path, "rb") as image_file:
                    # Read image data and encode in Base64
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:{image_type};base64,{base64_image}"}}
                                ]
                            }
                        ],
                        max_tokens=max_tokens
                    )

                    span.set_attribute("llm.output_messages.0.message.role", "assistant")
                    span.set_attribute("llm.output_messages.0.message.content", json.dumps(response.choices[0].message.content))
                    span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response.choices[0].message.content))
                    span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response.choices[0].message.content))

                    return {
                        "content": response.choices[0].message.content,
                        "success": True
                    }
            except FileNotFoundError:
                span.set_attribute("error.message", f"Image file not found: {image_path}")
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"Image file not found: {image_path}")
                span.set_attribute(SpanAttributes.RAW_OUTPUT, f"Image file not found: {image_path}")

                return {"error": f"Image file not found: {image_path}", "success": False}
            except Exception as e:
                span.set_attribute("error.message", str(e))
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(e))
                span.set_attribute(SpanAttributes.RAW_OUTPUT, str(e))

                return {
                    "error": str(e),
                    "success": False
                }
    
    def function_completion(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], model: str = "gpt-4.1") -> Dict[str, Any]:
        with tracer.start_as_current_span("function_completion", 
            attributes={
                SpanAttributes.INPUT_VALUE: json.dumps(messages),
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                SpanAttributes.RAW_INPUT: json.dumps(messages),
            }) as span:
            """Basic function calling completion with OpenAI"""
            try:
                # --- Add Detailed Input Logging --- 
                logger.debug(f"--- Function Completion Input ---")
                logger.debug(f"Model: {model}")
                # Log messages safely
                try:
                     logger.debug(f"Messages:\n{json.dumps(messages, indent=2)}")
                except Exception as log_e:
                     logger.warning(f"Could not serialize messages for debug logging: {log_e}")
                     logger.debug(f"Messages (raw): {messages}")
                # Log tools safely
                try:
                     logger.debug(f"Tools:\n{json.dumps(tools, indent=2)}")
                except Exception as log_e:
                     logger.warning(f"Could not serialize tools for debug logging: {log_e}")
                     logger.debug(f"Tools (raw): {tools}")
                logger.debug(f"--- End Function Completion Input ---")
                # --- End Detailed Input Logging --- 
                
                # Log input messages to span (existing code)
                for i, message in enumerate(messages):
                    if message.get("role") and message.get("content"):
                        span.set_attribute(f"llm.input_messages.{i}.message.role", message["role"])
                        span.set_attribute(f"llm.input_messages.{i}.message.content", message["content"])

                # Make the API call
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools
                )

                # Process successful response
                tool_calls = response.choices[0].message.tool_calls
                
                # Safely serialize tool_calls for logging/tracing
                tool_calls_json = None # Initialize
                if tool_calls:
                    try:
                        # Use model_dump() which is available on Pydantic models (like tool_calls)
                        tool_calls_list = [tc.model_dump() for tc in tool_calls]
                        tool_calls_json = json.dumps(tool_calls_list)
                    except Exception as json_e:
                        logger.warning(f"Could not serialize tool_calls for tracing: {json_e}")
                        tool_calls_json = "[Serialization Error]"
                else:
                    tool_calls_json = "[]" # Represent empty tool calls as empty JSON array
                
                # --- Use tool_calls_json for span attributes --- 
                span.set_attribute("llm.output_messages.0.message.role", "assistant")   
                span.set_attribute("llm.output_messages.0.message.content", tool_calls_json) # Use safe json
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, tool_calls_json) # Use safe json
                # Also update RAW_OUTPUT for consistency
                span.set_attribute(SpanAttributes.RAW_OUTPUT, tool_calls_json)
                # --- End span attribute update --- 

                return {
                    "tool_calls": tool_calls, # Return the actual objects
                    "success": True
                }
            except Exception as e:
                # Log the actual error from the API call
                error_message = f"{type(e).__name__}: {str(e)}"
                # Ensure full traceback is logged here to see where the API error happened
                logger.error(f"OpenAI function_completion API call failed: {error_message}", exc_info=True) 
                
                span.set_attribute("error.message", error_message)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, error_message) 
                # Set RAW_OUTPUT in error case too
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"error": error_message})) 
                return {
                    "error": error_message,
                    "success": False
                } 
    
    def generate_image(self, prompt: str, model: str = "gpt-image-1", size: str = "1024x1024", quality: str = "standard") -> Dict[str, Any]:
        """Generate an image using DALL-E"""
        with tracer.start_as_current_span("generate_image", 
            attributes={
                SpanAttributes.INPUT_VALUE: prompt,
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.LLM.value,
                SpanAttributes.RAW_INPUT: prompt,
            }) as span:
            try:
                response = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1
                )
                
                image_url = response.data[0].url
                
                span.set_attribute("image.generation.model", model)
                span.set_attribute("image.generation.size", size)
                span.set_attribute("image.generation.quality", quality)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, image_url)
                span.set_attribute(SpanAttributes.RAW_OUTPUT, image_url)
                
                return {
                    "image_url": image_url,
                    "success": True
                }
            except Exception as e:
                error_message = f"{type(e).__name__}: {str(e)}"
                logger.error(f"DALL-E image generation failed: {error_message}", exc_info=True)
                
                span.set_attribute("error.message", error_message)
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, error_message)
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps({"error": error_message}))
                
                return {
                    "error": error_message,
                    "success": False
                } 