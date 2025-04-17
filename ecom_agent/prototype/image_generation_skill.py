from typing import Dict, Any, Optional, Tuple
from gemini_integration import GeminiHelper

class ImageGenerationSkill:
    """Skill for generating images using Gemini"""
    
    def __init__(self):
        self.gemini_helper = GeminiHelper()
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the image generation skill"""
        try:
            # Generate the image
            image_path, result = self.gemini_helper.generate_image(query)
            
            if not result["success"]:
                return {
                    "type": "image_generation_error",
                    "error": result["error"]
                }
            
            return {
                "type": "image_generation",
                "image_path": image_path,
                "description": result.get("text", "Generated image based on your request"),
                "query": query
            }
            
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            } 