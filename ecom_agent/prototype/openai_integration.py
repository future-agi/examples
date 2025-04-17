import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIHelper:
    """Helper class for basic OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI()
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4", max_tokens: int = 1000) -> Dict[str, Any]:
        """Basic chat completion with OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            return {
                "content": response.choices[0].message.content,
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def vision_completion(self, image_path: str, prompt: str, model: str = "gpt-4-vision-preview", max_tokens: int = 300) -> Dict[str, Any]:
        """Basic vision completion with OpenAI"""
        try:
            with open(image_path, "rb") as image_file:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_file.read().hex()}"}}
                            ]
                        }
                    ],
                    max_tokens=max_tokens
                )
                return {
                    "content": response.choices[0].message.content,
                    "success": True
                }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def function_completion(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], model: str = "gpt-4") -> Dict[str, Any]:
        """Basic function calling completion with OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools
            )
            return {
                "tool_calls": response.choices[0].message.tool_calls,
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            } 