"""
AI prompt processing module for font search application.
This module handles the conversion of user text input into emotion and occasion weights.
"""

import os
import openai
from dotenv import load_dotenv
import json

# Import font database to access all emotions and occasions
from font_database import get_all_emotions, get_all_occasions

# Load environment variables (for OpenAI API key)
load_dotenv()

# Set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY", "")

def analyze_text_with_openai(text, emotions, occasions):
    """
    Use OpenAI to analyze text and generate weights for emotions and occasions.
    
    Args:
        text (str): User input text describing the purpose or occasion
        emotions (list): List of all possible emotions
        occasions (list): List of all possible occasions
        
    Returns:
        tuple: (emotion_weights, occasion_weights) dictionaries
    """
    if not openai_api_key:
        # If no API key is available, use fallback method
        return fallback_text_analysis(text, emotions, occasions)
    
    try:
        # Format emotions and occasions as comma-separated strings
        emotions_str = ", ".join(emotions)
        occasions_str = ", ".join(occasions)
        
        # Create the prompt for OpenAI
        prompt = f"""
        Analyze the following text that describes a purpose or occasion for font selection.
        
        Text: "{text}"
        
        Based on this text, assign weights (0.0 to 1.0) to the following emotions and occasions,
        where 0.0 means not relevant at all and 1.0 means extremely relevant.
        
        Emotions: {emotions_str}
        Occasions: {occasions_str}
        
        Return your analysis as a JSON object with two properties:
        1. "emotion_weights": A dictionary mapping emotions to weights
        2. "occasion_weights": A dictionary mapping occasions to weights
        
        Only include emotions and occasions with weights > 0.
        """
        
        # Call OpenAI API
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that analyzes text to determine relevant emotions and occasions for font selection."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract and parse the response
        result = response.choices[0].message.content
        
        # Extract JSON from the response
        json_str = result
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            json_str = result.split("```")[1].split("```")[0].strip()
            
        # Parse JSON
        weights = json.loads(json_str)
        
        return weights["emotion_weights"], weights["occasion_weights"]
        
    except Exception as e:
        print(f"Error using OpenAI API: {e}")
        # Fallback to simpler method if API call fails
        return fallback_text_analysis(text, emotions, occasions)

def fallback_text_analysis(text, emotions, occasions):
    """
    Fallback method for text analysis when OpenAI API is not available.
    Uses simple keyword matching to assign weights.
    
    Args:
        text (str): User input text describing the purpose or occasion
        emotions (list): List of all possible emotions
        occasions (list): List of all possible occasions
        
    Returns:
        tuple: (emotion_weights, occasion_weights) dictionaries
    """
    text = text.lower()
    
    # Initialize weights
    emotion_weights = {}
    occasion_weights = {}
    
    # Simple keyword matching for emotions
    for emotion in emotions:
        if emotion.lower() in text:
            emotion_weights[emotion] = 0.8
        elif any(word in text for word in emotion.lower().split('-')):
            emotion_weights[emotion] = 0.5
    
    # Simple keyword matching for occasions
    for occasion in occasions:
        if occasion.lower() in text:
            occasion_weights[occasion] = 0.8
        elif any(word in text for word in occasion.lower().split('-')):
            occasion_weights[occasion] = 0.5
    
    # Add some default weights if nothing matched
    if not emotion_weights:
        emotion_weights = {
            "neutral": 0.5,
            "modern": 0.3,
            "clean": 0.3
        }
    
    if not occasion_weights:
        occasion_weights = {
            "everyday": 0.5,
            "business": 0.3,
            "digital": 0.3
        }
    
    return emotion_weights, occasion_weights

def process_user_input(text):
    """
    Process user input text and return emotion and occasion weights.
    
    Args:
        text (str): User input text describing the purpose or occasion
        
    Returns:
        tuple: (emotion_weights, occasion_weights) dictionaries
    """
    # Get all possible emotions and occasions from the database
    emotions = get_all_emotions()
    occasions = get_all_occasions()
    
    # Analyze text to get weights
    emotion_weights, occasion_weights = analyze_text_with_openai(text, emotions, occasions)
    
    return emotion_weights, occasion_weights

# Example usage
if __name__ == "__main__":
    test_text = "I need a font for a children's birthday party invitation that is fun and playful."
    emotion_weights, occasion_weights = process_user_input(test_text)
    
    print("Emotion weights:")
    for emotion, weight in emotion_weights.items():
        print(f"{emotion}: {weight}")
    
    print("\nOccasion weights:")
    for occasion, weight in occasion_weights.items():
        print(f"{occasion}: {weight}")
