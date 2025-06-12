#!/usr/bin/env python3
"""
Script to generate realistic product images using AI (DALL-E/Gemini) for the e-commerce agent
"""

import os
import json
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openai_integration import OpenAIHelper
from gemini_integration import GeminiHelper

def create_product_prompt(product):
    """Create a detailed prompt for AI image generation"""
    name = product.get("name", "Product")
    description = product.get("description", "")
    category = product.get("category", "")
    colors = product.get("colors", [])
    
    # Create a detailed prompt
    prompt = f"A high-quality professional product photography image of {name}. "
    prompt += f"{description}. "
    
    # Add category-specific details
    if "clothing" in category.lower():
        prompt += "Fashion photography style, clean background, well-lit studio lighting. "
    elif "electronics" in category.lower():
        prompt += "Clean tech product photography, modern minimalist style, white background. "
    elif "footwear" in category.lower():
        prompt += "Professional shoe photography, clean white background, detailed textures. "
    elif "home" in category.lower() or "kitchen" in category.lower():
        prompt += "Home goods photography, lifestyle context, clean and modern. "
    else:
        prompt += "Professional product photography, clean white background. "
    
    # Add color information
    if colors and len(colors) > 0:
        main_color = colors[0]
        prompt += f"Primary color: {main_color}. "
    
    prompt += "Commercial quality, sharp focus, professional lighting, e-commerce style image."
    
    return prompt

def generate_image_dalle(product, openai_helper):
    """Generate image using DALL-E"""
    try:
        prompt = create_product_prompt(product)
        print(f"  🎨 DALL-E prompt: {prompt[:100]}...")
        
        result = openai_helper.generate_image(prompt)
        
        if result["success"]:
            # Download the image
            response = requests.get(result["image_url"])
            if response.status_code == 200:
                return response.content
        
        return None
        
    except Exception as e:
        print(f"  ❌ DALL-E error: {str(e)}")
        return None

def generate_image_gemini(product, gemini_helper):
    """Generate image using Gemini (if available)"""
    try:
        prompt = create_product_prompt(product)
        print(f"  🔮 Gemini prompt: {prompt[:100]}...")
        
        # Note: This would need to be implemented based on Gemini's image generation capabilities
        # For now, we'll return None as a placeholder
        print("  ⚠️ Gemini image generation not yet implemented")
        return None
        
    except Exception as e:
        print(f"  ❌ Gemini error: {str(e)}")
        return None

def create_fallback_image(product):
    """Create a fallback placeholder image using PIL"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with product-appropriate background
        colors = product.get("colors", [])
        bg_color = 'white'
        text_color = 'black'
        
        if colors and len(colors) > 0:
            color = colors[0].lower()
            if 'blue' in color:
                bg_color = '#E3F2FD'
                text_color = '#0D47A1'
            elif 'black' in color:
                bg_color = '#FAFAFA'
                text_color = '#212121'
            elif 'red' in color:
                bg_color = '#FFEBEE'
                text_color = '#C62828'
            elif 'green' in color:
                bg_color = '#E8F5E8'
                text_color = '#2E7D32'
        
        img = Image.new('RGB', (512, 512), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            desc_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
        
        # Draw product name
        name = product.get("name", "Product")
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), name, font=title_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (512 - text_width) // 2
        y = 200
        
        draw.text((x, y), name, fill=text_color, font=title_font)
        
        # Draw price
        price = product.get("price", 0)
        price_text = f"${price}"
        price_bbox = draw.textbbox((0, 0), price_text, font=desc_font)
        price_width = price_bbox[2] - price_bbox[0]
        
        x_price = (512 - price_width) // 2
        y_price = y + text_height + 30
        
        draw.text((x_price, y_price), price_text, fill=text_color, font=desc_font)
        
        # Add border
        draw.rectangle([20, 20, 492, 492], outline='lightgray', width=3)
        
        # Convert to bytes
        from io import BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    except Exception as e:
        print(f"  ❌ Fallback image creation failed: {str(e)}")
        return None

def main():
    """Generate realistic product images using AI"""
    
    print("🎨 Generating Realistic Product Images with AI")
    print("=" * 60)
    
    # Create directory
    os.makedirs("generated_products", exist_ok=True)
    
    # Load product database
    try:
        with open("product_database.json", "r") as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Error loading product database: {str(e)}")
        return
    
    # Initialize AI helpers
    openai_helper = None
    gemini_helper = None
    
    # Check for OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        try:
            openai_helper = OpenAIHelper()
            print("✅ DALL-E available")
        except Exception as e:
            print(f"⚠️ DALL-E initialization failed: {str(e)}")
    else:
        print("⚠️ OPENAI_API_KEY not found - DALL-E unavailable")
    
    # Check for Gemini (if needed)
    try:
        gemini_helper = GeminiHelper()
        print("✅ Gemini helper available")
    except Exception as e:
        print(f"⚠️ Gemini initialization failed: {str(e)}")
    
    print(f"\n🏭 Generating images for {len(products)} products...")
    
    success_count = 0
    dalle_count = 0
    fallback_count = 0
    
    for i, product in enumerate(products, 1):
        product_name = product.get("name", "Unknown Product")
        product_id = product.get("id", 0)
        
        print(f"\n📦 [{i}/{len(products)}] {product_name}")
        
        # Generate filename
        filename = f"generated_products/{product_name.lower().replace(' ', '_').replace('-', '_')}.png"
        
        # Skip if image already exists
        if os.path.exists(filename):
            print(f"  ✅ Image already exists: {filename}")
            success_count += 1
            continue
        
        image_data = None
        generation_method = "fallback"
        
        # Try DALL-E first
        if openai_helper:
            print("  🚀 Generating with DALL-E...")
            image_data = generate_image_dalle(product, openai_helper)
            if image_data:
                generation_method = "dalle"
                dalle_count += 1
        
        # Try Gemini if DALL-E failed
        if not image_data and gemini_helper:
            print("  🔮 Trying Gemini...")
            image_data = generate_image_gemini(product, gemini_helper)
            if image_data:
                generation_method = "gemini"
        
        # Fallback to PIL placeholder
        if not image_data:
            print("  🎭 Creating fallback placeholder...")
            image_data = create_fallback_image(product)
            if image_data:
                generation_method = "fallback"
                fallback_count += 1
        
        # Save the image
        if image_data:
            try:
                with open(filename, 'wb') as f:
                    f.write(image_data)
                print(f"  ✅ Saved ({generation_method}): {filename}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Failed to save: {str(e)}")
        else:
            print(f"  ❌ Failed to generate image for: {product_name}")
    
    # Summary
    print(f"\n📊 Generation Summary:")
    print(f"  ✅ Total successful: {success_count}/{len(products)}")
    print(f"  🎨 DALL-E generated: {dalle_count}")
    print(f"  🎭 Fallback placeholders: {fallback_count}")
    print(f"  📁 Images saved to: {os.path.abspath('generated_products')}")
    
    if success_count == len(products):
        print("\n🎉 All product images generated successfully!")
    else:
        print(f"\n⚠️ {len(products) - success_count} images failed to generate")

if __name__ == "__main__":
    main() 