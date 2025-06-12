#!/usr/bin/env python3

from search_skill import SearchSkill
from openai_integration import OpenAIHelper

def test_search_skill():
    # Test search skill directly
    search_skill = SearchSkill()
    context = {'query': 'jacket'}
    result = search_skill.execute('jacket', context)

    print('🔍 Search Skill Test: jacket')
    print('=' * 40)
    print(f'Query: {result["query"]}')
    print(f'Total Results: {result["total_results"]}')
    print('Products found:')
    for i, product in enumerate(result['results']):
        print(f'  {i+1}. {product["name"]} - ${product["price"]} (Rating: {product["rating"]})')
        if 'image_url' in product:
            print(f'     ✅ Image: {product["image_url"]}')
        else:
            print('     ❌ No image URL found')
    
    # Check database directly
    print('\n📦 Database Check:')
    jacket_products = [p for p in search_skill.product_database if 'jacket' in p['name'].lower()]
    for product in jacket_products:
        print(f'  - {product["name"]}: {"✅" if "image_url" in product else "❌"} Image URL')
        if "image_url" in product:
            print(f'    {product["image_url"]}')

if __name__ == "__main__":
    test_search_skill() 