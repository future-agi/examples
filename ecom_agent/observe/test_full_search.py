#!/usr/bin/env python3

from main import EcommerceAgent
import os

def test_full_search():
    print('🚀 Full Search Test: "looking for a jacket"')
    print('🔍' + '=' * 50)
    
    # Initialize the agent
    agent = EcommerceAgent()
    
    # Test the full search query
    query = "looking for a jacket"
    response, result = agent.process_query(query)
    
    print(f'Query: "{query}"')
    print(f'Response: {response[:200]}...')
    print(f'Result type: {type(result)}')
    
    if result:
        print(f'Result keys: {result.keys() if isinstance(result, dict) else "Not a dict"}')
        
        # Check for images
        if isinstance(result, dict):
            if 'product_images' in result:
                print(f'\n🖼️  Product Images Found: {len(result["product_images"])}')
                for i, img in enumerate(result['product_images']):
                    if img:
                        print(f'  {i+1}. {img}')
                        # Check if file exists
                        if os.path.exists(img):
                            print(f'     ✅ Image file exists')
                        else:
                            print(f'     ❌ Image file NOT found')
                    else:
                        print(f'  {i+1}. None/Empty')
            else:
                print('\n❌ No product_images key in result')
                
            if 'results' in result:
                print(f'\n📦 Search Results: {len(result["results"])} products')
                for i, product in enumerate(result['results']):
                    print(f'  {i+1}. {product["name"]}')
                    if 'image_url' in product:
                        print(f'     Image: {product["image_url"]}')
                    else:
                        print(f'     No image_url in product')
    else:
        print('❌ No result returned')
    
    print('\n' + '='*60)

if __name__ == "__main__":
    test_full_search() 