#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced product recommendation features
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import EcommerceAgent

def test_recommendations():
    """Test the new product recommendation system with images"""
    
    print("🛍️  Testing Enhanced E-commerce Agent with Product Images")
    print("=" * 60)
    
    # Initialize the agent
    agent = EcommerceAgent()
    
    # Test queries
    test_queries = [
        "I want to buy some athletic shoes for running",
        "Show me some electronics under $50", 
        "I need a black jacket for winter",
        "Recommend some blue clothing items",
        "What coffee maker would you suggest?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        try:
            response, result = agent.process_query(query)
            print(f"Response: {response}")
            
            if result and result.get("type") == "product_recommendation":
                recommendations = result.get("recommendations", {})
                if isinstance(recommendations, dict) and "recommendations" in recommendations:
                    products = recommendations["recommendations"]
                    images = result.get("product_images", [])
                    
                    print(f"\n📊 Found {len(products)} product recommendations")
                    print(f"🖼️  Generated {len([img for img in images if img and os.path.exists(img)])} product images")
                    
                    for j, product in enumerate(products):
                        print(f"  {j+1}. {product['name']} - ${product['price']}")
                        if product.get('image_url') and os.path.exists(product['image_url']):
                            print(f"     ✅ Image available: {product['image_url']}")
                        else:
                            print(f"     ❌ Image missing")
            
        except Exception as e:
            print(f"❌ Error testing query: {str(e)}")
    
    print(f"\n✅ Test completed! Check the generated_products folder for images.")
    print(f"📁 Generated images location: {os.path.abspath('generated_products')}")

def main():
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Using fallback image generation.")
        print("   Set your OpenAI API key in .env file for DALL-E image generation.")
    
    test_recommendations()

if __name__ == "__main__":
    main() 