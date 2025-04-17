from typing import Dict, Any, Optional, Tuple
from gemini_integration import GeminiHelper

class ImageEditingSkill:
    """Skill for editing images using Gemini"""
    
    def __init__(self):
        self.gemini_helper = GeminiHelper()
    
    def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the image editing skill"""
        try:
            # Get the image path from context
            image_path = context.get("image_path")
            if not image_path:
                return {
                    "type": "image_editing_error",
                    "error": "No image provided for editing"
                }
            
            # Edit the image
            image_path, result = self.gemini_helper.edit_image(image_path, query)
            
            if not result["success"]:
                return {
                    "type": "image_editing_error",
                    "error": result["error"]
                }
            
            return {
                "type": "image_editing",
                "image_path": image_path,
                "description": result.get("text", "Edited image based on your request"),
                "query": query
            }
            
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            } 