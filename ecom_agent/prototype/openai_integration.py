import os
import base64
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

tracer = trace.get_tracer(__name__)

# Load environment variables
load_dotenv()

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
                
                for i, message in enumerate(messages):
                    if message.get("role") and message.get("content"):
                        span.set_attribute(f"llm.input_messages.{i}.message.role", message["role"])
                        span.set_attribute(f"llm.input_messages.{i}.message.content", message["content"])

                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools
                )

                span.set_attribute("llm.output_messages.0.message.role", "assistant")   
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response.choices[0].message.tool_calls))
                span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response.choices[0].message.tool_calls))
                try:
                    message = response.choices[0].message
                    tool_calls = getattr(message, "tool_calls", None)
                    
                    if tool_calls and hasattr(tool_calls, "__iter__"):
                        for index, tool_call in enumerate(tool_calls):
                            # Record tool call ID if present
                            if hasattr(tool_call, "id") and tool_call.id is not None:
                                span.set_attribute(
                                    f"llm.output_messages.0.message.tool_calls.{index}.id", 
                                    tool_call.id
                                )
                            
                            # Record function details if present
                            if hasattr(tool_call, "function"):
                                function = tool_call.function
                                
                                if hasattr(function, "name") and function.name is not None:
                                    span.set_attribute(
                                        f"llm.output_messages.0.message.tool_calls.{index}.function.name",
                                        function.name
                                    )
                                
                                if hasattr(function, "arguments") and function.arguments is not None:
                                    span.set_attribute(
                                        f"llm.output_messages.0.message.tool_calls.{index}.function.arguments", 
                                        function.arguments
                                    )
                except Exception as e:
                    span.set_attribute("tool_calls_processing_error", str(e))
                    # We catch the error but continue execution to return the response

                return {
                    "tool_calls": response.choices[0].message.tool_calls,
                    "success": True
                }
            except Exception as e:
                span.set_attribute("error.message", str(e))
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(e))
                return {
                    "error": str(e),
                    "success": False
                } 