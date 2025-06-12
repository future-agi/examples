#!/usr/bin/env python3

from search_skill import SearchSkill
from product_recommender import ProductRecommender

def debug_databases():
    print('🔍 Database Debug Check')
    print('=' * 50)
    
    # Check search skill database
    search_skill = SearchSkill()
    print(f'Search skill database has {len(search_skill.product_database)} products')
    
    jacket_products_search = [p for p in search_skill.product_database if 'jacket' in p['name'].lower()]
    if jacket_products_search:
        jacket = jacket_products_search[0]
        print(f'Search skill jacket: {jacket["name"]} (ID: {jacket["id"]})')
        print(f'  Has image_url: {"✅" if "image_url" in jacket else "❌"}')
        if "image_url" in jacket:
            print(f'  Image URL: {jacket["image_url"]}')
    
    # Check product recommender database
    product_recommender = ProductRecommender()
    print(f'\nProduct recommender database has {len(product_recommender.product_database)} products')
    
    jacket_products_rec = [p for p in product_recommender.product_database if 'jacket' in p['name'].lower()]
    if jacket_products_rec:
        jacket = jacket_products_rec[0]
        print(f'Product recommender jacket: {jacket["name"]} (ID: {jacket["id"]})')
        print(f'  Has image_url: {"✅" if "image_url" in jacket else "❌"}')
        if "image_url" in jacket:
            print(f'  Image URL: {jacket["image_url"]}')
    
    # Check if they match
    print(f'\n🔄 Database Sync Check:')
    if len(search_skill.product_database) == len(product_recommender.product_database):
        print('✅ Same number of products')
    else:
        print('❌ Different number of products')
    
    # Check specific product matching
    search_ids = {p["id"]: p for p in search_skill.product_database}
    rec_ids = {p["id"]: p for p in product_recommender.product_database}
    
    matching_ids = set(search_ids.keys()) & set(rec_ids.keys())
    print(f'Matching product IDs: {len(matching_ids)} out of {len(search_ids)} search, {len(rec_ids)} recommender')

if __name__ == "__main__":
    debug_databases() 