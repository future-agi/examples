#!/usr/bin/env python3
"""
Test script to specifically test the jacket query from the user's screenshot
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import EcommerceAgent

def test_jacket_query():
    """Test the specific jacket query that was shown in the screenshot"""
    
    print("🧥 Testing Jacket Query: 'Hi do you have a jacket'")
    print("=" * 50)
    
    # Initialize the agent
    agent = EcommerceAgent()
    
    # Test the exact query from the screenshot
    query = "Hi do you have a jacket"
    
    print(f"🔍 Query: {query}")
    print("-" * 30)
    
    try:
        response, result = agent.process_query(query)
        print(f"Response Preview: {response[:200]}...")
        
        if result and isinstance(result, dict):
            print(f"\n📊 Result Type: {result.get('type', 'Unknown')}")
            
            # Check for images
            product_images = result.get('product_images', [])
            if product_images:
                valid_images = [img for img in product_images if img and os.path.exists(img)]
                print(f"🖼️  Found {len(valid_images)} product images:")
                for i, img_path in enumerate(valid_images, 1):
                    print(f"   {i}. {img_path}")
            else:
                print("❌ No product images found")
                
            # Check which skill was used
            if result.get("type") == "product_recommendation":
                print("✅ Used RECOMMENDATION skill (with images)")
            elif result.get("type") == "search_with_images":
                print("✅ Used SEARCH skill (with images)")
            elif result.get("type") == "search_results":
                print("⚠️  Used old SEARCH skill (no images)")
            else:
                print(f"ℹ️  Used skill: {result.get('type', 'Unknown')}")
                
        else:
            print("❌ No result data returned")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    print("\n" + "=" * 50)
    print("💡 For best results with images, try queries like:")
    print("   - 'Recommend a jacket'")
    print("   - 'I need a black jacket'") 
    print("   - 'Show me jackets'")
    print("   - 'What jackets do you have?'")

if __name__ == "__main__":
    test_jacket_query() 